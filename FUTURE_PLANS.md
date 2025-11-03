# Future Plans for Grading Assistant System

## Overview
This document outlines planned enhancements that are beyond the current scope but would significantly improve the system's capabilities.

---

## 1. Intelligent Example Selection for Few-Shot Learning

### Goal
Automatically select the most relevant few-shot examples based on context similarity, user preferences, assignment types, and historical performance.

### Current Implementation
- Random or most-recent selection from "good examples" pool
- User manually chooses number of examples (0-5)
- No context awareness or relevance filtering

### Planned Improvements

#### 1.1 Embedding-Based Similarity
**Description**: Use sentence transformers to find examples most similar to the current submission.

**Approach**:
- Generate embeddings for all saved feedback examples
- Generate embedding for incoming submission
- Use cosine similarity to rank examples by relevance
- Select top-N most similar examples

**Dependencies**:
- `sentence-transformers` library
- Pre-trained model (e.g., `all-MiniLM-L6-v2`)
- Vector storage for embeddings

**Benefits**:
- More contextually relevant examples
- Better LLM guidance for similar tasks
- Improved consistency across similar assignments

---

#### 1.2 Performance Tracking
**Description**: Track which examples lead to better human ratings and higher approval rates.

**Approach**:
- Store metrics for each example:
  - Times used in few-shot prompts
  - Subsequent human approval rate
  - User satisfaction scores
- Weight example selection by historical effectiveness
- Gradually phase out underperforming examples

**Storage Schema Addition**:
```sql
CREATE TABLE example_metrics (
    example_id TEXT PRIMARY KEY,
    times_used INTEGER DEFAULT 0,
    approvals INTEGER DEFAULT 0,
    rejections INTEGER DEFAULT 0,
    avg_user_rating REAL,
    last_used TIMESTAMP,
    effectiveness_score REAL
);
```

**Benefits**:
- Self-improving system
- Data-driven example selection
- Automatic quality control

---

#### 1.3 Adaptive User Preference Learning
**Description**: Learn which examples align best with each user's grading preferences.

**Approach**:
- Track user corrections per example type
- Build user-specific preference profiles
- Personalize example selection per user
- Detect preference patterns (strict vs lenient, style preferences, etc.)

**Implementation Ideas**:
- Cluster user corrections to identify grading styles
- Use collaborative filtering (similar to recommendation systems)
- A/B test different examples to optimize selection

**Benefits**:
- Personalized grading assistance
- Faster alignment with user expectations
- Reduced need for corrections over time

---

#### 1.4 Category Matching
**Description**: Match examples to assignment types, courses, and grading criteria categories.

**Approach**:
- Tag examples with metadata:
  - Assignment type (essay, code, math, lab report, etc.)
  - Subject area (CS, English, Math, etc.)
  - Grading focus (content, structure, style, etc.)
- Filter examples by matching tags before selection
- Combine with similarity scoring for best results

**Schema Addition**:
```sql
ALTER TABLE corrections ADD COLUMN assignment_type TEXT;
ALTER TABLE corrections ADD COLUMN subject_area TEXT;
ALTER TABLE corrections ADD COLUMN grading_focus TEXT;
```

**Benefits**:
- Domain-specific guidance
- More relevant examples for diverse assignments
- Better cross-course support

---

## 2. Implementation Roadmap

### Phase 1: Embedding Infrastructure (Est. 2-3 days)
1. Add `sentence-transformers` to dependencies
2. Create embedding generation module
3. Store embeddings in database (as BLOB or separate vector DB)
4. Build similarity search function

### Phase 2: Performance Tracking (Est. 1-2 days)
1. Create `example_metrics` table
2. Update `save_correction` to track usage
3. Implement effectiveness scoring algorithm
4. Add UI to display example performance stats

### Phase 3: Smart Selection Algorithm (Est. 2-3 days)
1. Combine similarity + effectiveness scoring
2. Implement weighted selection
3. Add configuration options (similarity weight, effectiveness weight, diversity)
4. Test and tune selection parameters

### Phase 4: User Preference Learning (Est. 3-4 days)
1. Build user profile system
2. Track corrections per user
3. Implement preference detection
4. Personalize example selection

### Phase 5: Category Matching (Est. 1-2 days)
1. Add tagging UI for examples
2. Implement tag-based filtering
3. Auto-suggest tags based on assignment content
4. Integrate with existing selection algorithm

---

## 3. Technical Dependencies

### Required Libraries
```txt
sentence-transformers>=2.2.0  # Semantic embeddings
faiss-cpu>=1.7.4              # Fast similarity search (optional, for large scale)
scikit-learn>=1.0.0           # Clustering, metrics
numpy>=1.21.0                 # Vector operations
```

### Alternative Approaches
- **OpenAI Embeddings**: Use OpenAI API for embeddings (requires API key, not local)
- **FAISS**: For large-scale vector search (>10k examples)
- **Chromadb**: Lightweight vector database (easier than FAISS)
- **Simple Cosine**: NumPy-based for small datasets (<1k examples)

---

## 4. Evaluation Metrics

### Success Criteria
- **Relevance**: Selected examples should have high similarity to submission (>0.7 cosine similarity)
- **Effectiveness**: Examples should lead to fewer user corrections (<10% correction rate)
- **Diversity**: Avoid selecting too-similar examples (min 0.3 distance between selected examples)
- **Speed**: Selection should complete in <500ms

### A/B Testing Plan
1. **Baseline**: Random selection from good examples
2. **Test A**: Similarity-only selection
3. **Test B**: Effectiveness-only selection
4. **Test C**: Combined similarity + effectiveness
5. **Test D**: Full system with user preferences

**Metrics to Track**:
- User correction rate
- Average user rating
- Time to acceptance
- Example diversity scores

---

## 5. Future-Future Plans

### 5.1 Fine-Tuning Local Models
- Use collected feedback to fine-tune local LLMs
- Create domain-specific grading models
- Reduce reliance on few-shot learning

### 5.2 Active Learning
- System requests human feedback on uncertain gradings
- Prioritize learning from edge cases
- Automatic gap detection in example library

### 5.3 Multi-Modal Support
- Handle image-based submissions (diagrams, handwriting)
- Extract text from complex PDFs with tables/figures
- Support code execution and testing

### 5.4 Collaborative Grading
- Share example libraries across instructors
- Federated learning across institutions
- Privacy-preserving knowledge sharing

---

## 6. Open Questions

1. **Embedding Model**: Which model best captures grading-relevant semantics?
2. **Effectiveness Metric**: How to weight speed vs accuracy vs user satisfaction?
3. **Cold Start**: How to bootstrap with few examples?
4. **Drift Detection**: How to detect when grading preferences change over time?
5. **Explainability**: How to show users why certain examples were selected?

---

## 7. References & Inspiration

- **Few-Shot Learning**: Brown et al., "Language Models are Few-Shot Learners" (GPT-3 paper)
- **Retrieval-Augmented Generation**: Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
- **Example Selection**: Rubin et al., "Learning to Retrieve Prompts for In-Context Learning"
- **Semantic Search**: Reimers & Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"

---

**Last Updated**: November 2, 2025  
**Status**: Planning Phase  
**Priority**: Medium (after core features stabilize)


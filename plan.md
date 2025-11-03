make a grading system to grade college level students homework 
1. it is based on the local large language model, and finds a model that has good cognition, large context size, and knowledge of programming code and scientific knowledges. it can also switch between a few candidates.
2. the interface should both support text input, and file uploader. it should be able to support plain text format, pdf, ms word, and images.
3. it can also accept multiple files from the file system, grade in batches in the same grading criteria, including checking plagarisms between the batches, and have a list to check the results as the final report
4. it shall have a way to combine multiple information, like the homework assignment instruction, grading criteria, grading output (A-E or number), plagarism identification, AI agent prompt keyword(used to detect if used a word embeded in the instruction), and potentila some other extra requirements to form the system prompt.
5. It should have a profile system to create the requirements for multiple homework and a way that the system prompts can be grouped into courses. It can use the existing prompt as a template to create a new one. there is a module that manage, browse, update, organize the prompts.
6. The output of the grading includes: grades (based on the prompt requirements), grading reasons(highlights and deduction reason), if identified plagarism (if the plagarism check is selected), and my feedbacks for future fine-tuning or in-context learning to improve the alignment to the human. 
7. a system to parsing the grading criteria to prompts.
8. a system to parsing the llm output to the output, and a way to read the raw output. provide a way that can accept user's input for further in-context learning or fine-tuning to align with the output formt
9. a system to fine-tuning the model
10. a system to in-context learning based on few-shot prompt focusing on the output format and the output quality
11. it have a way to search the internet if it needs to determine external knowledge, like the references
12. a way to export the grading results of a batch input
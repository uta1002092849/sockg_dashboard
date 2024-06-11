from langchain.chains import GraphCypherQAChain
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.prompts import FewShotPromptTemplate
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_chroma import Chroma
from templates.examples import examples
from templates.prefix_prompt import prefix_prompt
from models.llms import gemini_pro
from neo4j_connector.graph import neo4j_graph

from models.embeddings import llama3_embeddings


example_prompt = PromptTemplate.from_template(
    "User input: {question}\nCypher query: {query}"
)

example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    llama3_embeddings,
    Chroma(),
    k=5,
    input_keys=["question"],
)


prompt = FewShotPromptTemplate(
    example_selector = example_selector,
    example_prompt = example_prompt,
    prefix = prefix_prompt,
    suffix="User input: {question}\nCypher query: ",
    input_variables=["question", "schema"],
)


chain = GraphCypherQAChain.from_llm(
    llm=gemini_pro,
    graph=neo4j_graph,
    verbose=True,
    validate_cypher=True,
    cypher_prompt=prompt,
    return_intermediate_steps=True,
)

def generate_cypher(prompt_text):
    try:
        response = chain.invoke({"query":prompt_text})
    except Exception as e:
        response = {"result": "Sorry, I can only answer questions related to the sockg dataset"}
    
    # try one more time if 'intermediate_steps' is not in response
    if 'intermediate_steps' not in response:
        try:
            response = chain.invoke({"query":prompt_text})
        except Exception as e:
            response = {"result": "Sorry, I can only answer questions related to the sockg dataset"}
    
    # check if intermediate steps are present in response
    if 'intermediate_steps' not in response:
        raise Exception("Sorry, I could not process your request. Please try to rephrase your question or try again later.")
    constructed_cypher = response['intermediate_steps'][0]['query']
    constructed_context = response['intermediate_steps'][1]['context']
    final_response = response['result']
    
    return {"constructed_cypher": constructed_cypher, "constructed_context": constructed_context, "final_response": final_response}

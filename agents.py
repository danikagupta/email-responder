import streamlit as st

from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import PromptTemplate

from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser

from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults




GROQ_LLM = ChatGroq(
            model="llama3-70b-8192",
            api_key=st.secrets["GROQ_API_KEY"]
        )


#
# Email Category Generator
#

prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a Email Categorizer Agent You are a master at understanding what a customer wants when they write an email and are able to categorize it in a useful way

     <|eot_id|><|start_header_id|>user<|end_header_id|>
    Conduct a comprehensive analysis of the email provided and categorize into one of the following categories:
        price_equiry - used when someone is asking for information about pricing \
        customer_complaint - used when someone is complaining about something \
        product_enquiry - used when someone is asking for information about a product feature, benefit or service but not about pricing \\
        customer_feedback - used when someone is giving feedback about a product \
        off_topic when it doesnt relate to any other category \


            Output a single cetgory only from the types ('price_equiry', 'customer_complaint', 'product_enquiry', 'customer_feedback', 'off_topic') \
            eg:
            'price_enquiry' \

    EMAIL CONTENT:\n\n {initial_email} \n\n
    <|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """,
    input_variables=["initial_email"],
)

email_category_generator = prompt | GROQ_LLM | StrOutputParser()

def test_email_category_generator(EMAIL):
    result = email_category_generator.invoke({"initial_email": EMAIL}).strip("'")
    print(f"Result is :{repr(result)}:")
    assert result == "customer_feedback"

#
# Research Router
#

research_router_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are an expert at reading the initial email and routing web search or directly to a draft email. \n

    Use the following criteria to decide how to route the email: \n\n

    If the initial email only requires a simple response
    Just choose 'draft_email'  for questions you can easily answer, prompt engineering, and adversarial attacks.
    If the email is just saying thank you etc then choose 'draft_email'

    You do not need to be stringent with the keywords in the question related to these topics. Otherwise, use research-info.
    Give a binary choice 'research_info' or 'draft_email' based on the question. Return the a JSON with a single key 'router_decision' and
    no premable or explaination. use both the initial email and the email category to make your decision
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    Email to route INITIAL_EMAIL : {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category"],
)

research_router = research_router_prompt | GROQ_LLM | JsonOutputParser()

def test_research_router(EMAIL):
    email_category = 'customer_feedback'
    result = research_router.invoke({"initial_email": EMAIL, "email_category":email_category})
    print(result)
    assert result == {"router_decision": "draft_email"}

#
# Search keywords
#

search_keyword_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are a master at working out the best keywords to search for in a web search to get the best info for the customer.

    given the INITIAL_EMAIL and EMAIL_CATEGORY. Work out the best keywords that will find the best
    info for helping to write the final email.

    Return a JSON with a single key 'keywords' with no more than 3 keywords and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category"],
)

search_keyword_chain = search_keyword_prompt | GROQ_LLM | JsonOutputParser()

def test_search_keyword_chain(EMAIL):
    email_category = 'customer_feedback'
    result = search_keyword_chain.invoke({"initial_email": EMAIL, "email_category":email_category})
    print(f"Test-Search-Keyword-chain returned :{result}:")
    # Results vary. This is just an example.
    #assert result == {"keywords": ["resort", "staff", "wonderful"]}

#
# Draft writer
#

draft_writer_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Email Writer Agent take the INITIAL_EMAIL below  from a human that has emailed our company email address, the email_category \
            that the categorizer agent gave it and the research from the research agent and \
            write a helpful email in a thoughtful and friendly way.

            If the customer email is 'off_topic' then ask them questions to get more information.
            If the customer email is 'customer_complaint' then try to assure we value them and that we are addressing their issues.
            If the customer email is 'customer_feedback' then try to assure we value them and that we are addressing their issues.
            If the customer email is 'product_enquiry' then try to give them the info the researcher provided in a succinct and friendly way.
            If the customer email is 'price_equiry' then try to give the pricing info they requested.

            You never make up information that hasn't been provided by the research_info or in the initial_email.
            Always sign off the emails in appropriate manner and from Sarah the Resident Manager.

            Return the email a JSON with a single key 'email_draft' and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    RESEARCH_INFO: {research_info} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category","research_info"],
)

draft_writer_chain = draft_writer_prompt | GROQ_LLM | JsonOutputParser()

def test_draft_writer_chain(EMAIL):
    email_category = 'customer_feedback'
    research_info = None
    result = draft_writer_chain.invoke({"initial_email": EMAIL, "email_category":email_category,"research_info":research_info})
    print(f"Test-draft-writer returns :{result}:")
    #assert result == {"email_draft": "Dear Paul, \n\n I am so glad you had a wonderful stay at our resort last week. We really appreciate your feedback. \n\n Best, Sarah the Resident Manager"}

#
# Rewrite Router
#

rewrite_router_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are an expert at evaluating the emails that are draft emails for the customer and deciding if they
    need to be rewritten to be better. \n

    Use the following criteria to decide if the DRAFT_EMAIL needs to be rewritten: \n\n

    If the INITIAL_EMAIL only requires a simple response which the DRAFT_EMAIL contains then it doesn't need to be rewritten.
    If the DRAFT_EMAIL addresses all the concerns of the INITIAL_EMAIL then it doesn't need to be rewritten.
    If the DRAFT_EMAIL is missing information that the INITIAL_EMAIL requires then it needs to be rewritten.

    Give a binary choice 'rewrite' (for needs to be rewritten) or 'no_rewrite' (for doesn't need to be rewritten) based on the DRAFT_EMAIL and the criteria.
    Return the a JSON with a single key 'router_decision' and no premable or explaination. \
    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n
    EMAIL_CATEGORY: {email_category} \n
    DRAFT_EMAIL: {draft_email} \n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category","draft_email"],
)

rewrite_router = rewrite_router_prompt | GROQ_LLM | JsonOutputParser()

def test_rewrite_router(EMAIL):
    email_category = 'customer_feedback'
    draft_email = "Yo we can't help you, best regards Sarah"
    result = rewrite_router.invoke({"initial_email": EMAIL, "email_category":email_category, "draft_email":draft_email})
    print(f"Test-rewrite-router returns :{result}:")
    #assert result == {"router_decision": "rewrite"}

#
# Draft Email Analysis
#

draft_analysis_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Quality Control Agent read the INITIAL_EMAIL below  from a human that has emailed \
    our company email address, the email_category that the categorizer agent gave it and the \
    research from the research agent and write an analysis of how the email.

    Check if the DRAFT_EMAIL addresses the customer's issued based on the email category and the \
    content of the initial email.\n

    Give feedback of how the email can be improved and what specific things can be added or change\
    to make the email more effective at addressing the customer's issues.

    You never make up or add information that hasn't been provided by the research_info or in the initial_email.

    Return the analysis a JSON with a single key 'draft_analysis' and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    INITIAL_EMAIL: {initial_email} \n\n
    EMAIL_CATEGORY: {email_category} \n\n
    RESEARCH_INFO: {research_info} \n\n
    DRAFT_EMAIL: {draft_email} \n\n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email","email_category","research_info"],
)

draft_analysis_chain = draft_analysis_prompt | GROQ_LLM | JsonOutputParser()

def test_draft_analysis_chain(EMAIL):
    email_category = 'customer_feedback'
    research_info = None
    draft_email = "Yo we can't help you, best regards Sarah"
    result = draft_analysis_chain.invoke({"initial_email": EMAIL,
                                 "email_category":email_category,
                                 "research_info":research_info,
                                 "draft_email": draft_email})
    print(f"Test-draft-analysis-chain returns :{result}:")
    #assert result == {"draft_analysis": "The email is not helpful and needs to be rewritten to be more customer focused."}

#
# Rewrite Email with Analysis
#

rewrite_email_prompt = PromptTemplate(
    template="""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
    You are the Final Email Agent read the email analysis below from the QC Agent \
    and use it to rewrite and improve the draft_email to create a final email.


    You never make up or add information that hasn't been provided by the research_info or in the initial_email.

    Return the final email as JSON with a single key 'final_email' which is a string and no premable or explaination.

    <|eot_id|><|start_header_id|>user<|end_header_id|>
    EMAIL_CATEGORY: {email_category} \n\n
    RESEARCH_INFO: {research_info} \n\n
    DRAFT_EMAIL: {draft_email} \n\n
    DRAFT_EMAIL_FEEDBACK: {email_analysis} \n\n
    <|eot_id|><|start_header_id|>assistant<|end_header_id|>""",
    input_variables=["initial_email",
                     "email_category",
                     "research_info",
                     "email_analysis",
                     "draft_email",
                     ],
)

rewrite_chain = rewrite_email_prompt | GROQ_LLM | JsonOutputParser()

def test_rewrite_chain(EMAIL):
    email_category = 'customer_feedback'
    research_info = None
    draft_email = "Yo we can't help you, best regards Sarah"
    email_analysis = "The email is not helpful and needs to be rewritten to be more customer focused."
    result = rewrite_chain.invoke({"initial_email": EMAIL,
                                 "email_category":email_category,
                                 "research_info":research_info,
                                 "draft_email": draft_email,
                                "email_analysis":email_analysis})
    print(f"Test-rewrite-chain returns :{result}:")
    #assert result == {"final_email": "Dear Paul, \n\n I am so glad you had a wonderful stay at our resort last week. We really appreciate your feedback. \n\n Best, Sarah the Resident Manager"}

#
# Web search
#
web_search_tool=TavilySearchResults(k=1)

#
# Main - for testing
#

if __name__ == "__main__":
    EMAIL = """HI there, \n
    I am emailing to say that I had a wonderful stay at your resort last week. \n

    I really appreciate what your staff did\n

    Thanks,\n
    Paul
    """
    test_email_category_generator(EMAIL)
    test_research_router(EMAIL)
    test_search_keyword_chain(EMAIL)
    test_draft_writer_chain(EMAIL)
    test_rewrite_router(EMAIL)
    test_draft_analysis_chain(EMAIL)
    test_rewrite_chain(EMAIL)
    print("All tests passed")
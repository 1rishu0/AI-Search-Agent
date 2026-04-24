# this is going to allow us to load in the environment variables that we have defined in this dot env file.
# Langgraph is a graph which allow us a bunch of different nodes that are connected to each other and to flow some state or some data through that graph where each kind of node in the graph can modify or update that data. So, we are going to have some state which is going to store all of the information that our agent need to have access to, and as we run through these different stages or nodes in our graph, we will be populating that state, where at the end of that graph, we have this final answer which we can present to the user.
# the init_chat_model is a really quick way to initialize an inline graph

from dotenv import load_dotenv
from typing import Annotated, List
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from web_operations import *
from prompts import *


load_dotenv()

llm = init_chat_model("gpt-4o")


# now we are writing out the state that we are going to pass through our graph, when we have the state, we'll kind of understand the data that we need to come up with and find and then we can start creating this graph and making the connections between these nodes and then we can start actually kind of populating the graph by writing the different implementations.
class State(TypedDict):
    # inside of here we are going to start by having a list of messages, Now these messages are essentially the messages that our user is sending into this graph that will then process and start getting the information for coming up with an answer for it.
    # `messages` is a list that will hold all message objects (e.g., HumanMessage, AIMessage, ToolMessage).
    # The `Annotated` wrapper tells LangGraph how to handle updates to this field.
    # Specifically, `add_messages` is a reducer function that knows how to merge/appends new messages to the existing list
    # instead of simply overwriting it—crucial for maintaining conversation history across multiple node executions.
    messages: Annotated[List, add_messages]
    user_question: str | None
    google_results: str | None
    bing_results: str | None
    reddit_results: str | None
    # we are going to select a bunch of results from reddit, and then we are going to pass these results to LLM and it is going to select which of these URLs we actually want to process further
    selected_reddit_urls: list[str] | None
    # this is going to be the data for those selected URLs
    reddit_post_data: list | None
    # Now below is all the LLM Analysis that we are going to done on the above results
    google_analysis: str | None
    bing_analysis: str | None
    reddit_analysis: str | None
    tavily_reddit_results: str | None
    tavily_reddit_analysis: str | None
    final_answer: str | None


# we need to define a Python class and then pass that to an llm and tell the llm that it needs to give us an output that's in this particular format.
class RedditURLAnalysis(BaseModel):
    selected_urls: List[str] = Field(description="List of Reddit URLs that contain valuable information for answering the user's question")


def google_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Google for: {user_question}")

    google_results = serp_search(query=user_question, engine="google")

    return {"google_results": google_results}


def bing_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Bing for: {user_question}")

    bing_results = serp_search(query=user_question, engine="bing")

    return {"bing_results": bing_results}


def reddit_search(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Reddit for: {user_question}")

    reddit_results = reddit_search_api(user_question)

    return {"reddit_results": reddit_results}

# In this function we take the user questions and reddit results from the state class and construct the llm with structured output and after that put that question and reddit result in the url analysis function to get the message return for both system and user , then started invoking the llm with that message and get the selected url from that result and print it properly and return it.
def analyze_reddit_posts(state: State):
    user_question = state.get("user_question", "")
    reddit_results = state.get("reddit_results", "")

    if not reddit_results:
        return {"selected_reddit_urls": []}

    structured_llm = llm.with_structured_output(RedditURLAnalysis)
    messages = get_reddit_url_analysis_messages(user_question, reddit_results)

    try:
        analysis = structured_llm.invoke(messages)
        selected_urls = analysis.selected_urls

        print("Selected URLs: ")
        for i, url in enumerate(selected_urls, 1):
            print(f"    {i}.  {url}")

    except Exception as e:
        print(e)
        selected_urls = []

    return {"selected_reddit_urls": selected_urls}


# In this function we are getting the selected reddit urls from the state and if it is empty the we leave it just right that , after that we are retrieving the reddit post by inputting the selected reddit urls in the reddit_post_retrieval function , after getting post we return it to State.
def retrieve_reddit_posts(state: State):
    print("Getting reddit post comments")

    selected_urls = state.get("selected_reddit_urls",[])

    if not selected_urls:
        return {"reddit_post_data": []}

    print(f"Processing {len(selected_urls)} Reddit URLs")

    reddit_post_data = reddit_post_retrieval(selected_urls)

    if reddit_post_data:
        print(f"Successfully got {len(reddit_post_data)} posts")
    else:
        print("Failed to get post data")
        reddit_post_data = []

    return {"reddit_post_data": reddit_post_data}


# this function take user_question and google results from state and with inputting these variable in the get_google_analysis_messages function from prompts module to get the messages for invoking the LLM and return its content
def analyze_google_results(state: State):
    print("Analyzing google search results")

    user_question = state.get("user_question", "")
    google_results = state.get("google_results", "")

    messages = get_google_analysis_messages(user_question, google_results)
    reply = llm.invoke(messages)

    return {"google_analysis": reply.content}


# this function take user_question and bing results from state and with inputting these variable in the get_bing_analysis_messages function from prompts module to get the messages for invoking the LLM and return its content
def analyze_bing_results(state: State):
    print("Analyzing bing search results")

    user_question = state.get("user_question", "")
    bing_results = state.get("bing_results", "")

    messages = get_bing_analysis_messages(user_question, bing_results)
    reply = llm.invoke(messages)

    return {"bing_analysis": reply.content}


# this function take user_question, reddit results and reddit_post_data from state and with inputting these variable in the get_reddit_analysis_messages function from prompts module to get the messages for invoking the LLM and return its content
def analyze_reddit_results(state: State):
    print("Analyzing reddit search results")

    user_question = state.get("user_question","")
    reddit_results = state.get("reddit_results", "")
    reddit_post_data = state.get("reddit_post_data", "")

    messages = get_reddit_analysis_messages(user_question, reddit_results, reddit_post_data)
    reply = llm.invoke(messages)

    return {"reddit_analysis": reply.content}


def tavily_reddit_search_node(state: State):
    user_question = state.get("user_question", "")
    print(f"Searching Reddit via Tavily for: {user_question}")

    tavily_reddit_results = tavily_reddit_search(user_question)

    return {"tavily_reddit_results": tavily_reddit_results}


def analyze_tavily_reddit_results(state: State):
    print("Analyzing Tavily Reddit search results")

    user_question = state.get("user_question", "")
    tavily_reddit_results = state.get("tavily_reddit_results", "")

    if not tavily_reddit_results:
        return {"tavily_reddit_analysis": ""}

    messages = get_tavily_reddit_analysis_messages(user_question, str(tavily_reddit_results))
    reply = llm.invoke(messages)

    return {"tavily_reddit_analysis": reply.content}


def synthesize_analyses(state: State):
    print("Combine all results together")

    user_question = state.get("user_question", "")
    google_analysis = state.get("google_analysis", "")
    bing_analysis = state.get("bing_analysis", "")
    reddit_analysis = state.get("reddit_analysis", "")
    tavily_reddit_analysis = state.get("tavily_reddit_analysis", "")

    messages = get_synthesis_messages(user_question, google_analysis, bing_analysis, reddit_analysis, tavily_reddit_analysis)
    reply = llm.invoke(messages)
    final_answer = reply.content

    return {"final_answer": final_answer, "messages":[{"role":"assistant", "content": final_answer}]}


graph_builder = StateGraph(State)

graph_builder.add_node("google_search", google_search)
graph_builder.add_node("bing_search", bing_search)
graph_builder.add_node("reddit_search", reddit_search)
graph_builder.add_node("analyze_reddit_posts", analyze_reddit_posts)
graph_builder.add_node("retrieve_reddit_posts", retrieve_reddit_posts)
graph_builder.add_node("analyze_google_results", analyze_google_results)
graph_builder.add_node("analyze_bing_results", analyze_bing_results)
graph_builder.add_node("analyze_reddit_results", analyze_reddit_results)
graph_builder.add_node("tavily_reddit_search", tavily_reddit_search_node)
graph_builder.add_node("analyze_tavily_reddit_results", analyze_tavily_reddit_results)
graph_builder.add_node("synthesize_analyses", synthesize_analyses)

graph_builder.add_edge(START, "google_search")
graph_builder.add_edge(START, "bing_search")
graph_builder.add_edge(START, "reddit_search")
graph_builder.add_edge(START, "tavily_reddit_search")

graph_builder.add_edge("google_search", "analyze_reddit_posts")
graph_builder.add_edge("bing_search", "analyze_reddit_posts")
graph_builder.add_edge("reddit_search", "analyze_reddit_posts")

graph_builder.add_edge("analyze_reddit_posts", "retrieve_reddit_posts")

graph_builder.add_edge("retrieve_reddit_posts", "analyze_google_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_bing_results")
graph_builder.add_edge("retrieve_reddit_posts", "analyze_reddit_results")

graph_builder.add_edge("analyze_google_results", "synthesize_analyses")
graph_builder.add_edge("analyze_bing_results", "synthesize_analyses")
graph_builder.add_edge("analyze_reddit_results", "synthesize_analyses")

graph_builder.add_edge("tavily_reddit_search", "analyze_tavily_reddit_results")
graph_builder.add_edge("analyze_tavily_reddit_results", "synthesize_analyses")

graph_builder.add_edge("synthesize_analyses", END)

graph = graph_builder.compile()


def run_chatbot():
    print("Multi-Source Resource Agent")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("Ask me anything: ")
        if user_input.lower() == 'exit':
            print('bye')
            break

        # we need to kind a initialize the starting state
        state = {
            "messages": [{"role": "user", "content": user_input}],
            "user_question": user_input,
            "google_results": None,
            "bing_results": None,
            "reddit_results": None,
            "selected_reddit_urls": None,
            "reddit_post_data": None,
            "google_analysis": None,
            "bing_analysis": None,
            "reddit_analysis": None,
            "tavily_reddit_results": None,
            "tavily_reddit_analysis": None,
            "final_answer": None,
        }

        print("\nStarting Parallel research process...")
        print("Launching Google, Bing, Reddit, and Tavily Reddit searches...\n")

        final_state = graph.invoke(state)

        if final_state.get("final_answer"):
            print(f"\nFinal Answer:\n{final_state.get('final_answer')}\n")

        print("-" * 80)


if __name__ == '__main__':
    run_chatbot()


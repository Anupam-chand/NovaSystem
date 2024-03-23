import os
from dotenv import load_dotenv
# from langchain_community.utilities import GoogleSerperAPIWrapper
# from langchain_community.llms import ollama
from crewai import Agent, Crew, Task, Process
from crewai_tools import BaseTool, SerperDevTool, tool
from langchain.agents import load_tools
from langchain_community.chat_models import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from uuid import uuid4
import spacy
# import anthropic
# import openai
import requests


# Load environment variables and set up necessary API keys and wrappers
load_dotenv()
# google_search = GoogleSerperAPIWrapper()

# Set up the necessary API keys and .env variables
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY") or "your_fallback_serper_api_key"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") or "your_fallback_openai_api_key"

# Initialize spaCy NLP model for keyword extraction
nlp = spacy.load("en_core_web_sm")

# Setting up language model for CrewAI agents
openai_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=.5)
anthropic_llm = ChatAnthropic(model_name="claude-3-haiku-20240307", temperature=0.5) # or any other model "claude-3-haiku-20240307" "claude-3-sonnet-20240229" "claude-3-opus-20240229"

# Load human agents and tools
human_tools = load_tools(["human"])
search_tool = SerperDevTool()

# Function to append text to a file
def append_to_file(filename, text):
    with open(filename, 'a') as file:
        file.write(text + '\n')

## Set up custom tools for the Tribunal
# Custom tools
class MyCustomTool(BaseTool):
    name: str = "My Custom Tool"
    description: str = "A custom tool for specific tasks."

    def _run(self, argument: str) -> str:
        # Custom logic here
        return f"Custom tool executed with argument: {argument}"

class TextPreprocessTool(BaseTool):
    # Provide type annotations for overridden fields
    name: str = "TextPreprocessTool"
    description: str = "Cleans, extracts keywords, and summarizes text, returning a unified JSON."

    def _run(self, text: str) -> dict:
        """Process text to extract keywords, summarize, and clean, encapsulating all steps within."""
        doc = nlp(text)
        
        # Clean text: Removing stop words and punctuation for a simplified version of text
        cleaned_text = ' '.join(token.text for token in doc if not token.is_stop and not token.is_punct)
        
        # Extract keywords: Tokens not stopped or punctuated
        keywords = list(set(token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and token.is_alpha))
        
        # Summarize text: Here simplification could be generating sentences from the first N keywords for demonstration
        summary = ' '.join(keywords[:10]) if len(keywords) > 10 else ' '.join(keywords)
        
        return {
            "cleaned_text": cleaned_text,
            "keywords": keywords,
            "summary": summary
        }

@tool("IntegrationWithGivenAPI")
def integration_tool(api_endpoint: str) -> str:
    """
    Makes a GET request to a specified API endpoint and returns the response as a string.

    Args:
        api_endpoint (str): The URL of the API endpoint to which the GET request will be sent.

    Returns:
        str: The response from the API call.
    """
    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX or 5XX
        results = response.text  # For simplicity, returning the raw response text
        return results
    except requests.RequestException as e:
        return f"Error making API call: {e}"

# @tool("FileManagerTool")
# class FileManager:
#     """
#     A FileManager tool for performing CRUD operations on files.
#     """

#     @staticmethod
#     def create(file_path: str, content: str) -> str:
#         """Creates a new file with the specified content.
        
#         Args:
#             file_path (str): The path where the file will be created.
#             content (str): The content to write to the file.
        
#         Returns:
#             str: A message indicating the outcome.
#         """
#         try:
#             with open(file_path, 'w') as file:
#                 file.write(content)
#             return f"File created at: {file_path}"
#         except Exception as e:
#             return f"Failed to create file: {str(e)}"

#     @staticmethod
#     def read(file_path: str) -> str:
#         """Reads the content of a specified file.
        
#         Args:
#             file_path (str): The path of the file to read.
        
#         Returns:
#             str: The content of the file.
#         """
#         try:
#             with open(file_path, 'r') as file:
#                 return file.read()
#         except Exception as e:
#             return f"Failed to read file: {str(e)}"

#     @staticmethod
#     def update(file_path: str, content: str) -> str:
#         """Updates the content of an existing file.
        
#         Args:
#             file_path (str): The path of the file to update.
#             content (str): The new content to write to the file.
        
#         Returns:
#             str: A message indicating the outcome.
#         """
#         try:
#             with open(file_path, 'w') as file:
#                 file.write(content)
#             return f"File updated at: {file_path}"
#         except Exception as e:
#             return f"Failed to update file: {str(e)}"

#     @staticmethod
#     def delete(file_path: str) -> str:
#         """Deletes a specified file.
        
#         Args:
#             file_path (str): The path of the file to delete.
        
#         Returns:
#             str: A message indicating the outcome.
#         """
#         try:
#             os.remove(file_path)
#             return f"File deleted: {file_path}"
#         except Exception as e:
#             return f"Failed to delete file: {str(e)}"



# Create an instance of the custom tool
# my_custom_tool = MyCustomTool()
text_preprocess_tool = TextPreprocessTool()
# file_manager_tool = FileManager()

# Set up the agents and tasks for the Tribunal
## Set up demo agents and tasks
# Creating a senior researcher agent with memory and verbose mode
researcher = Agent(
  role='Senior Researcher',
  goal='Uncover groundbreaking technologies in {topic}',
  llm=anthropic_llm,
  max_iter=5,
  max_rpm=10,
  verbose=True,
  memory=True,
  backstory=(
    "Driven by curiosity, you're at the forefront of"
    "innovation, eager to explore and share knowledge that could change"
    "the world."
  ),
  tools=[search_tool, text_preprocess_tool],
  allow_delegation=True
)

# Creating a writer agent with custom tools and delegation capability
writer = Agent(
  role='Writer',
  goal='Narrate compelling tech stories about {topic}',
  llm=anthropic_llm,
  max_iter=5,
  max_rpm=10,
  verbose=True,
  memory=True,
  backstory=(
    "With a flair for simplifying complex topics, you craft"
    "engaging narratives that captivate and educate, bringing new"
    "discoveries to light in an accessible manner."
  ),
  tools=[search_tool, text_preprocess_tool],
  allow_delegation=False
)

# Research task
research_task = Task(
  description=(
    "Identify the next big trend in {topic}."
    "Focus on identifying pros and cons and the overall narrative."
    "Your final report should clearly articulate the key points"
    "its market opportunities, and potential risks."
  ),
  expected_output='A comprehensive 3 paragraphs long report on the latest AI trends.',
  tools=[search_tool, text_preprocess_tool],
  agent=researcher,
)

# Writing task with language model configuration
write_task = Task(
  description=(
    "Compose an insightful article on {topic}."
    "Focus on the latest trends and how it's impacting the industry."
    "This article should be easy to understand, engaging, and positive."
  ),
  expected_output='A 4 paragraph article on {topic} advancements formatted as markdown.',
  tools=[search_tool, text_preprocess_tool,],
  agent=writer,
  async_execution=False,
  output_file='new-blog-post.md'  # Example of output customization
)


# Forming the tech-focused crew with enhanced configurations
crew = Crew(
  agents=[researcher, writer],
  tasks=[research_task, write_task],
  process=Process.sequential  # Optional: Sequential task execution is default
)

######## Example of task execution with enhanced feedback with the above agents and tasks
# Starting the task execution process
request = input("What is your request? ")
document_path = "experimental_research_findings.txt"
result = crew.kickoff(inputs={'topic': request})
run_id = uuid4().hex

# Append the research findings to the file
append_to_file(document_path, f"Run: {run_id}\nRequest: {request}\n# Research Findings #")
append_to_file(document_path, result)
append_to_file(document_path, "Task completed successfully.")
######## Uncomment the above lines to run the example ########
##############################################################


class Arbiter(Agent):
    """Foundation for specific Arbiters with corrected initialization."""
    def __init__(self, role, goal, backstory, tools, llm, function_calling_llm, max_iter, max_rpm, verbose, allow_delegation, step_callback, memory):
        if tools is None:
            tools = []
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            function_calling_llm=function_calling_llm,
            max_iter=max_iter,
            max_rpm=max_rpm,
            verbose=verbose,
            allow_delegation=allow_delegation,
            step_callback=step_callback,
            memory=memory
        )

# Continuing with the Arbiter definitions...

class ArbiterOfPossibility(Arbiter):
    """Arbiter for assessing possibilities and outcomes."""
    def __init__(self):
        super().__init__(
            role="Arbiter of Possibility",
            goal="To assess the feasibility and potential outcomes of proposed projects, ensuring they are grounded in reality and have a tangible pathway to success.",
            backstory="""With a keen analytical mind and a pragmatic approach, you've always been able to sift through ideas to find those with true potential. 
                        Your career spans various industries, giving you a broad perspective on what it takes to turn concepts into realities.
                        Your passion is to assess the feasibility and potential outcomes of proposed projects, ensuring they are grounded in reality and have a tangible pathway to success.""",
            llm=openai_llm,
            function_calling_llm=openai_llm,
            max_iter=5,
            max_rpm=10,
            verbose=True,
            allow_delegation=True,
            step_callback=None,
            memory=False
        )

class ArbiterOfPermission(Arbiter):
    """Arbiter for determining permissions within constraints."""
    def __init__(self):
        super().__init__(
            role="Arbiter of Permission",
            goal="To ensure all initiatives comply with legal, ethical, and organizational standards, safeguarding the integrity and values of our endeavors.",
            backstory="""As a digital legal advocate with a passion for ethics in technology, you bring a deep understanding of the regulatory landscape and a commitment to upholding high moral standards in all projects.
                        Your history of navigating complex legal and ethical challenges has made you a trusted advisor in the organization, ensuring all initiatives comply with legal, ethical, and organizational standards, safeguarding the integrity and values of our endeavors.
                        It is your passion to ensure all initiatives comply with legal, ethical, and organizational standards, safeguarding the integrity and values of our endeavors.""",
            llm=openai_llm,
            function_calling_llm=openai_llm,
            max_iter=5,
            max_rpm=10,
            verbose=True,
            allow_delegation=True,
            step_callback=None,
            memory=False
        )

class ArbiterOfPreference(Arbiter):
    """Arbiter for gauging stakeholder preferences and desirability."""
    def __init__(self):
        super().__init__(
            role="Arbiter of Preference",
            goal="To gauge stakeholder preferences and market demands, ensuring our projects align with user expectations and have the potential for positive impact.",
            backstory="""With a background in market research and user experience design, you have a pulse on consumer trends and a talent for predicting what will resonate with our audience.
                        Your expertise in gauging stakeholder preferences and market demands has been instrumental in shaping successful products and initiatives, ensuring they align with user expectations and have the potential for positive impact.
                        Your passion is to gauge stakeholder preferences and market demands, ensuring our projects align with user expectations and have the potential for positive impact.""",
            llm=openai_llm,
            function_calling_llm=openai_llm,
            max_iter=5,
            max_rpm=10,
            verbose=True,
            allow_delegation=True,
            step_callback=None,
            memory=False
        )

# Instantiate each Arbiter
possibility_arbiter = ArbiterOfPossibility()
permission_arbiter = ArbiterOfPermission()
preference_arbiter = ArbiterOfPreference()
print(f"Arbiters instantiated: {possibility_arbiter}, {permission_arbiter}, {preference_arbiter}")


# Note: Replace `search_tool` with the actual tool instances your agents need to perform their tasks.
# arbiter_crew = Crew(
#     agents=[possibility_arbiter, permission_arbiter, preference_arbiter],
#     tasks=tasks,
#     process=Process.sequential,
#     verbose=True,
# )

# # Kick off the decision-making process
# arbiter_crew.kickoff()
##### Demo of the arbiter process #####
##############################################################

class Magistrate(Agent):
    def __init__(self, llm, function_calling_llm, max_iter, max_rpm, verbose, step_callback, memory):
        super().__init__(
            role="Magistrate",
            goal="To make informed decisions by considering the recommendations of the Arbiters.",
            backstory="""As the Magistrate, your role is to oversee the decision-making process and ensure that all perspectives are considered.
                        With a deep understanding of the Tribunal system and the expertise of the Arbiters, you are responsible for receiving requests,
                        delegating tasks to the Arbiters, and making the final decision based on their recommendations.""",
            llm=llm,
            function_calling_llm=function_calling_llm,
            max_iter=max_iter,
            max_rpm=max_rpm,
            verbose=verbose,
            step_callback=step_callback,
            memory=memory,
            # tools=[search_tool] + human_tools
        )

    # def receive_request(self, request):
    #     self.request = request
    #     print(f"Magistrate received request: {request}")

    # def delegate_to_arbiters(self):
    #     tasks = []
    #     for arbiter in self.arbiters:
    #         task = Task(
    #             description=f"Assess {arbiter.role.lower()} for: {self.request}",
    #             agent=arbiter,
    #             tools=arbiter.tools,
    #         )
    #         tasks.append(task)
    #     print(f"Delegated {len(tasks)} tasks to {len(self.arbiters)} Arbiters.")
    #     return tasks

    # def make_decision(self, recommendations):
    #     # Placeholder logic for making the final decision based on Arbiter recommendations
    #     decision = f"Final decision based on Arbiter recommendations:\n"
    #     for arbiter, recommendation in recommendations.items():
    #         decision += f"{arbiter.role}: {recommendation}\n"
    #     return decision

    # def process_request(self, request):
    #     self.receive_request(request)
    #     tasks = self.delegate_to_arbiters()
    #     recommendations = {}
    #     for task in tasks:
    #         result = task.execute()
    #         recommendations[task.agent] = result
    #     final_decision = self.make_decision(recommendations)
    #     print("Final decision:", final_decision)
    #     return final_decision

# Instantiate the Magistrate
magistrate = Magistrate(
    llm=openai_llm,
    function_calling_llm=openai_llm,
    max_iter=5,
    max_rpm=10,
    verbose=True,
    step_callback=None,
    memory=False
)

# Define the tasks and expected outputs for the Arbiters
request = input("State your request for the Arbiters: ")
# Setup tasks with expected_output for each task
assess_request = Task(
        description=f'Assess the following request and make a plan of action to address it: {request}',
        agent=magistrate,
        # tools=[search_tool, text_preprocess_tool, file_manager_tool],
        tools=[search_tool, text_preprocess_tool],
        expected_output=f'A plan of action to address the request: {request}.',
    )
    
assess_possibilities = Task(
        description=f'Assess possibilities for: {request}',
        agent=possibility_arbiter,
        # tools=[search_tool, text_preprocess_tool, file_manager_tool],
        tools=[search_tool, text_preprocess_tool],
        expected_output=f'A detailed analysis of the feasibility and potential outcomes for: {request}.',
    )

verify_permissions = Task(
        description=f'Verify permissions for: {request}',
        agent=permission_arbiter,
        # tools=[search_tool, text_preprocess_tool, file_manager_tool],
        tools=[search_tool, text_preprocess_tool],
        expected_output=f'A report on legal and ethical permissions concerning: {request}.',
    )

gauge_preverences = Task(
        description=f'Gauge preferences for: {request}',
        agent=preference_arbiter,
        # tools=[search_tool, text_preprocess_tool, file_manager_tool],
        tools=[search_tool, text_preprocess_tool],
        expected_output=f'An assessment of stakeholder and market preferences for: {request}.',
    )
    
final_ruling = Task(
        description=f'Make a final ruling report on: {request}',
        agent=magistrate,
        # tools=[search_tool, text_preprocess_tool, file_manager_tool],
        tools=[search_tool, text_preprocess_tool],
        expected_output=f'A final ruilng report based on the recommendations of the Arbiters for: {request}.',
        context = [assess_request, assess_possibilities, verify_permissions, gauge_preverences]
    )

tasks = [assess_request, assess_possibilities, verify_permissions, gauge_preverences, final_ruling]

Tribunal = Crew(
    agents=[possibility_arbiter, permission_arbiter, preference_arbiter, magistrate], # Uncomment to include the magistrate for human interaction
    # agents=[possibility_arbiter, permission_arbiter, preference_arbiter],
    tasks=tasks,
    manager_llm=openai_llm,
    process=Process.hierarchical,
)

### Example of processing a request with the Magistrate
print("#" * 50)
print(f"Processing request: {request}")
final_decision = Tribunal.kickoff(inputs={'request': request})
print(final_decision)
append_to_file(document_path, f"Run: {run_id}\nRequest: {request}\n# Tribunal Decision #")
##### Demo of the magistrate process #####
##############################################################
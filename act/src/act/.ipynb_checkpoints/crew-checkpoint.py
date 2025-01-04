from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_groq import ChatGroq
from langchain.llms import Ollama
from litellm import completion

ollama_llm =Ollama(model='mistral', api_base="http://localhost:11434")

@CrewBase
class Act():
	"""Act crew"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self) -> None:
		#self.groq_llm = ChatGroq(temperature= 0, model_name= "groq/mixtral-8x7b-32768")
		self.groq_llm = ollama_llm


	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			llm=self.groq_llm
		)
	@agent
	def accountant(self) -> Agent:
		return Agent(
			config=self.agents_config['accountant'],
			llm=self.groq_llm
		)
	@agent
	def recommender(self) -> Agent:
		return Agent(
			config=self.agents_config['recommender'],
			llm=self.groq_llm
		)
	@agent
	def blogger(self) -> Agent:
		return Agent(
			config=self.agents_config['blogger'],
			llm=self.groq_llm
		)
	@task
	def researcher_task(self) -> Task:
		return Task(
			config=self.tasks_config['researcher_task'],
			agent=self.researcher()
		)

	@task
	def accountant_task(self) -> Task:
		return Task(
			config=self.tasks_config['accountant_task'],
			agent=self.accountant()
		)

	@task
	def recommender_task(self) -> Task:
		return Task(
			config=self.tasks_config['recommender_task'],
			agent=self.recommender()
		)

	@task
	def blogger_task(self) -> Task:
		return Task(
			config=self.tasks_config['blogger_task'],
			agent=self.blogger()
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the Act crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
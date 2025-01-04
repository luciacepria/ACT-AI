from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from langchain_groq import ChatGroq
from litellm import completion
import yfinance as yf


#ollama_llm =completion(model='ollama/mistral', api_base="http://localhost:11434")

@CrewBase
class Act():
	"""Act crew"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self, ticker) -> None:
		self.groq_llm = ChatGroq(temperature= 0, model_name= "groq/mixtral-8x7b-32768")
		self.ticker = ticker
		self.stock = yf.Ticker(ticker)
		#self.groq_llm = ollama_llm


	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			llm=self.groq_llm
		)

	def fetch_stock_data(self, symbol: str):
		stock = yf.Ticker(symbol)
		stock_info = stock.history(period="5d")  # Last 5 days of stock data
		return stock_info

	def researcher_research_on_finance(self, symbol: str):
		stock_data = self.fetch_stock_data(symbol)
		return stock_data

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
		stock_symbol = self.ticker
		stock_data = self.researcher_research_on_finance(stock_symbol)
		return Task(
			config=self.tasks_config['researcher_task'],
			agent=self.researcher(),
			result=stock_data  # Include the fetched stock data in the task result
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
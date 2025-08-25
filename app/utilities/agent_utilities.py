from typing import List, Union, Any
from langchain.chains import LLMChain
from langchain.prompts import BasePromptTemplate
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.prompts import StringPromptTemplate
from langchain.schema import AgentAction, AgentFinish, SystemMessage, PromptValue, BaseMessage
from langchain.tools import Tool

from app.utilities.time_utilities import get_current_time_in_tz


class CustomPromptValue(PromptValue):
    text: str

    def to_string(self) -> str:
        """Return prompt as string."""
        return self.text

    def to_messages(self) -> List[BaseMessage]:
        """Return prompt as messages."""
        return [SystemMessage(content=self.text)]


class CustomPromptTemplate(StringPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format_prompt(self, **kwargs: Any) -> PromptValue:
        """Create Chat Messages."""
        return CustomPromptValue(text=self.format(**kwargs))

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)


class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if a tool should be executed
        if "Action:" in llm_output:
            # Strip whitespace from tool name for comparison
            tool_name = llm_output.split("Action: ")[-1].split("\n")[0].strip()
            tool_input = "" 
            return AgentAction(tool=tool_name, tool_input=tool_input, log=llm_output)
        else:
            return AgentFinish(return_values={"output": llm_output.strip()}, log=llm_output)



output_parser = CustomOutputParser()


def get_agent_executor(tools, instance_id, llm, history, primer_before, primer_after):
    time_primer = f"It is: {get_current_time_in_tz(instance_id)}"
    history = '\n'.join([message['role'] + ':' + message['content'] for message in history])
    template_with_history = time_primer + primer_before + """

        Your job is to select the optimum tool to that alligns with the customer message in the context of the conversation history. 

        You have access to the following tools:

        {tools}

        Base the tool use on tool description. 


        IMPORTANT: Respond using the following format:

        Action: the action to take, should be one of [{tool_names}]
        Action Input: 'submit'                   //<-Always the same input

        YOU MUST INCLUDE ACTION AND ACTION INPUT IN THE ABOVE FORM IN YOUR RESPONSE.
    ----------------------------------------
        History:
        """ + f"{history}" + """"
    ----------------------------------------
        Latest Message: {input}
    ----------------------------------------
        Respond using the following format:

        Action: the action to take, should be one of [{tool_names}]
        Action Input: 'submit'                   //<-Always the same input

        """ + primer_after

    prompt_with_history = CustomPromptTemplate(
        template=template_with_history,
        tools=tools,
        input_variables=["input", "intermediate_steps", "history"]
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt_with_history)

    tool_names = [tool.name for tool in tools]

    agent = LLMSingleActionAgent(
        llm_chain=llm_chain,
        output_parser=output_parser,
        stop=["\nAction:"],
        allowed_tools=tool_names
    )

    agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, max_execution_time=2)
    return agent_executor

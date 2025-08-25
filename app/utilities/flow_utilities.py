import os

from langchain.agents import AgentExecutor
from langflow import load_flow_from_json


class FlowUtilities:

    @staticmethod
    def get_file_name(client_id: str) -> str:
        return "clients/" + client_id + ".json"

    @staticmethod
    def write_flow_to_file(flow: str, client_id: str):
        directory = 'clients'
        if not os.path.exists(directory):
            os.makedirs(directory)

        print("write flow file")
        file_name = FlowUtilities.get_file_name(client_id)
        with open(file_name, 'w') as f:
            f.write(flow)
        return file_name

    @staticmethod
    def call_flow_with_user_input(flow: AgentExecutor, user_input: str) -> str:
        return flow(user_input)['output']

    @staticmethod
    def get_method_from_flow(flow: str, client_id: str, user_input: str) -> str:
        file_name = FlowUtilities.write_flow_to_file(flow, client_id)
        flow = load_flow_from_json(file_name)
        return FlowUtilities.call_flow_with_user_input(flow, user_input)

import os
import json

# Use a local file for state persistence in EC2 environment
STATE_FILE = "bot_state.json"

class BotState:
    START = "START"
    WELCOME = "WELCOME"
    PROVIDE_ERROR = "PROVIDE_ERROR"
    SELECT_ERROR = "SELECT_ERROR"
    SELECT_FUNCTION_AREA = "SELECT_FUNCTION_AREA"
    SOLUTION_PROVIDED = "SOLUTION_PROVIDED"

class StateManager:
    def __init__(self):
        self.states = {}
        self.load_state()

    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    self.states = json.load(f)
            except:
                self.states = {}

    def save_state(self):
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(self.states, f)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def get_state(self, user_id):
        return self.states.get(user_id, {}).get("state", BotState.START)

    def get_data(self, user_id):
        return self.states.get(user_id, {}).get("data", {})

    def set_state(self, user_id, state, data=None):
        self.states[user_id] = {
            "state": state,
            "data": data if data is not None else self.get_data(user_id)
        }
        self.save_state()

    def reset_state(self, user_id):
        if user_id in self.states:
            del self.states[user_id]
            self.save_state()

    def update_data(self, user_id, data_update):
        current_data = self.get_data(user_id)
        current_data.update(data_update)
        self.set_state(user_id, self.get_state(user_id), current_data)

# Global instances
state_manager = StateManager()

def update_state(user_id, **kwargs):
    current_data = state_manager.get_data(user_id)
    current_data.update(kwargs)
    state_manager.set_state(user_id, state_manager.get_state(user_id), current_data)

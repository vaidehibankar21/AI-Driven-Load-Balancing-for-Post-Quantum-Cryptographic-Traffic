import random

class QLearningBalancerAgent:
    def __init__(self, num_nodes, alpha=0.5, gamma=0.5, epsilon=0.3):
        self.num_nodes = num_nodes
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.95
        self.q_table = {}
        # ✅ OPTIMISTIC INIT — higher than any expected reward
        # Forces AI to try every node at least once
        self.initial_q = 500.0

    def _init_state(self, state):
        if state not in self.q_table:
            self.q_table[state] = {j: self.initial_q for j in range(self.num_nodes)}

    def select_action(self, state):
        self._init_state(state)
        q_vals = dict(self.q_table[state])
        explored = random.uniform(0, 1) < self.epsilon
        if explored:
            action = random.randint(0, self.num_nodes - 1)
        else:
            best_val = max(q_vals.values())
            best = [k for k, v in q_vals.items() if v == best_val]
            action = random.choice(best)
        return action, {
            "state": list(state),
            "q_values": {f"node{i+1}": round(q_vals[i], 3) for i in range(self.num_nodes)},
            "epsilon": round(self.epsilon, 4),
            "mode": "explore" if explored else "exploit",
            "reason": (f"Random exploration (ε={self.epsilon:.3f})"
                       if explored else
                       f"Max Q-value: {best_val:.2f} at node{action+1}"),
        }

    def update_q_table(self, state, action, reward):
        self._init_state(state)
        old_q = self.q_table[state][action]
        new_q = old_q + self.alpha * (reward - old_q)
        self.q_table[state][action] = new_q
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return {
            "old_q": round(old_q, 2),
            "new_q": round(new_q, 2),
            "reward": round(reward, 2),
            "formula": f"Q += {self.alpha} × ({reward:.2f} − {old_q:.2f}) = {new_q:.2f}",
        }

    def reset(self):
        self.q_table = {}
        self.epsilon = 0.3

    def get_q_values(self, state):
        self._init_state(state)
        return dict(self.q_table[state])

    def snapshot(self):
        return {
            "epsilon": round(self.epsilon, 4),
            "q_table": {str(k): v for k, v in self.q_table.items()},
        }
"""
Custom GridWorld Environment for Reinforcement Learning
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class MyGridWorld(gym.Env):
    """
    Custom 3x3 GridWorld Environment
    
    Grid Layout (state numbers):
    0  1  2
    3  4  5
    6  7  8
    
    - Diamond at state 8 (reward: +10)
    - Mountains at states 4, 7 (reward: -2)
    - Other states reward: -1
    - Actions: 0=left, 1=down, 2=right, 3=up
    """
    
    def __init__(self, render_mode=None):
        super().__init__()
        
        # Environment parameters
        self.grid_size = 3
        self.n_states = self.grid_size * self.grid_size
        
        # Special states
        self.diamond_state = 8
        self.mountain_states = [4, 7]
        
        # Action and observation spaces
        self.action_space = spaces.Discrete(4)  # 0=left, 1=down, 2=right, 3=up
        self.observation_space = spaces.Discrete(self.n_states)
        
        # Render mode and metadata
        self.render_mode = render_mode
        self.metadata = {
            "render_modes": ["human", "rgb_array", "text"],
            "render_fps": 4,
        }
        self.fig = None
        self.ax = None
        
        # Initialize state
        self.current_state = None
        
    def _get_coordinates(self, state):
        """Convert state number to (row, col) coordinates"""
        row = state // self.grid_size
        col = state % self.grid_size
        return row, col
    
    def _get_state(self, row, col):
        """Convert (row, col) coordinates to state number"""
        return row * self.grid_size + col
    
    def _is_valid_position(self, row, col):
        """Check if position is within grid bounds"""
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size
    
    def _get_next_state(self, state, action):
        """Get next state given current state and action"""
        row, col = self._get_coordinates(state)
        
        # Action mapping: 0=left, 1=down, 2=right, 3=up
        if action == 0:  # left
            new_col = col - 1
            new_row = row
        elif action == 1:  # down
            new_col = col
            new_row = row + 1
        elif action == 2:  # right
            new_col = col + 1
            new_row = row
        elif action == 3:  # up
            new_col = col
            new_row = row - 1
        else:
            raise ValueError(f"Invalid action: {action}")
        
        # Check bounds - if move is invalid, stay in current state
        if self._is_valid_position(new_row, new_col):
            return self._get_state(new_row, new_col)
        else:
            return state  # Stay in current state if move is invalid
    
    def _get_reward(self, state):
        """Get reward for being in a state"""
        if state == self.diamond_state:
            return 10
        elif state in self.mountain_states:
            return -2
        else:
            return -1
    
    def _is_terminal(self, state):
        """Check if state is terminal (diamond reached)"""
        return state == self.diamond_state
    
    def reset(self, seed=None, options=None):
        """Reset environment to initial state"""
        super().reset(seed=seed)
        
        # Start at state 0 (top-left corner)
        self.current_state = 0
        
        return self.current_state, {}
    
    def step(self, action):
        """Take a step in the environment"""
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action: {action}")
        
        # Get next state
        next_state = self._get_next_state(self.current_state, action)
        
        # Get reward
        reward = self._get_reward(next_state)
        
        # Check if terminal
        terminated = self._is_terminal(next_state)
        
        # Update current state
        self.current_state = next_state
        
        return next_state, reward, terminated, False, {}
    
    def render(self):
        """Render the environment"""
        if self.render_mode == 'rgb_array':
            return self._render_rgb_array()
        elif self.render_mode == 'human':
            self._render_human()
        else:
            # Text rendering
            self._render_text()
    
    def _render_text(self):
        """Simple text rendering"""
        print(f"\nCurrent State: {self.current_state}")
        grid = [['.' for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Mark special states
        for state in range(self.n_states):
            row, col = self._get_coordinates(state)
            if state == self.diamond_state:
                grid[row][col] = 'D'  # Diamond
            elif state in self.mountain_states:
                grid[row][col] = 'M'  # Mountain
            elif state == self.current_state:
                grid[row][col] = 'A'  # Agent
        
        # Print grid
        for row in grid:
            print(' '.join(row))
        print()
    
    def _render_rgb_array(self):
        """Render as RGB array for matplotlib"""
        if self.fig is None:
            self.fig, self.ax = plt.subplots(figsize=(6, 6))
        
        self.ax.clear()
        self.ax.set_xlim(0, self.grid_size)
        self.ax.set_ylim(0, self.grid_size)
        self.ax.set_aspect('equal')
        
        # Draw grid
        for i in range(self.grid_size + 1):
            self.ax.axhline(i, color='black', linewidth=1)
            self.ax.axvline(i, color='black', linewidth=1)
        
        # Draw states
        for state in range(self.n_states):
            row, col = self._get_coordinates(state)
            x, y = col, self.grid_size - 1 - row  # Flip y for proper display
            
            # Draw background
            if state == self.diamond_state:
                rect = patches.Rectangle((x, y), 1, 1, linewidth=1, 
                                       edgecolor='black', facecolor='gold', alpha=0.7)
                self.ax.add_patch(rect)
                self.ax.text(x + 0.5, y + 0.5, 'D', ha='center', va='center', 
                           fontsize=20, fontweight='bold')
            elif state in self.mountain_states:
                rect = patches.Rectangle((x, y), 1, 1, linewidth=1, 
                                       edgecolor='black', facecolor='brown', alpha=0.7)
                self.ax.add_patch(rect)
                self.ax.text(x + 0.5, y + 0.5, 'M', ha='center', va='center', 
                           fontsize=20, fontweight='bold', color='white')
            
            # Draw agent
            if state == self.current_state:
                circle = patches.Circle((x + 0.5, y + 0.5), 0.3, 
                                      facecolor='blue', edgecolor='darkblue', linewidth=2)
                self.ax.add_patch(circle)
            
            # Add state numbers
            self.ax.text(x + 0.1, y + 0.1, str(state), ha='left', va='bottom', 
                        fontsize=10, color='gray')
        
        self.ax.set_title('GridWorld Environment', fontsize=16, fontweight='bold')
        self.ax.set_xlabel('Actions: 0=Left, 1=Down, 2=Right, 3=Up', fontsize=12)
        
        # Remove ticks
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Convert to RGB array
        self.fig.canvas.draw()
        buf = np.frombuffer(self.fig.canvas.tostring_rgb(), dtype=np.uint8)
        buf = buf.reshape(self.fig.canvas.get_width_height()[::-1] + (3,))
        
        return buf
    
    def _render_human(self):
        """Render for human viewing"""
        rgb_array = self._render_rgb_array()
        plt.imshow(rgb_array)
        plt.axis('off')
        plt.show()
    
    def close(self):
        """Close rendering"""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None
    
    def _build_transition_matrix(self):
        """
        Build the transition probability matrix P for dynamic programming.
        P[s][a] = [(probability, next_state, reward, terminated), ...]
        """
        self.P = {}
        
        for state in range(self.n_states):
            self.P[state] = {}
            
            for action in range(4):  # 4 actions: left, down, right, up
                next_state = self._get_next_state(state, action)
                reward = self._get_reward(next_state)
                terminated = self._is_terminal(next_state)
                
                # Since movements are deterministic, probability is always 1.0
                self.P[state][action] = [(1.0, next_state, reward, terminated)]
    
    def get_transition_matrix(self):
        """Return the transition matrix for external algorithms"""
        return self.P
    
    def get_reward_matrix(self):
        """Return reward matrix R[s][a] for convenience"""
        R = np.zeros((self.n_states, 4))
        for state in range(self.n_states):
            for action in range(4):
                next_state = self._get_next_state(state, action)
                R[state][action] = self._get_reward(next_state)
        return R

def register_gridworld():
    """Register the MyGridWorld environment with gymnasium"""
    try:
        register(
            id='MyGridWorld',
            entry_point='utils:MyGridWorld',  # Points to this module
            max_episode_steps=100,
        )
        print("MyGridWorld environment registered successfully!")
    except gym.error.Error:
        # Environment already registered
        print("MyGridWorld environment already registered.")
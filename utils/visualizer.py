import plotly.graph_objects as go
from plotly.subplots import make_subplots

class Visualizer:
    """Creates visualizations for algorithm results."""
    
    @staticmethod
    def plot_fitness_convergence(history):
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=list(range(len(history['best_fitness']))),
            y=history['best_fitness'],
            mode='lines',
            name='Best Fitness',
            line=dict(color='blue', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=list(range(len(history['avg_fitness']))),
            y=history['avg_fitness'],
            mode='lines',
            name='Average Fitness',
            line=dict(color='lightblue', width=2)
        ))
        
        fig.update_layout(
            title='Fitness Convergence Over Generations',
            xaxis_title='Generation',
            yaxis_title='Fitness Score',
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def plot_constraint_violations(history):
        fig = make_subplots(rows=2, cols=1,
                           subplot_titles=('Hard Constraint Violations', 
                                         'Soft Constraint Violations'))
        
        fig.add_trace(go.Scatter(
            x=list(range(len(history['hard_violations']))),
            y=history['hard_violations'],
            mode='lines',
            name='Hard Violations',
            line=dict(color='red', width=2)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=list(range(len(history['soft_violations']))),
            y=history['soft_violations'],
            mode='lines',
            name='Soft Violations',
            line=dict(color='orange', width=2)
        ), row=2, col=1)
        
        fig.update_xaxes(title_text='Generation', row=2, col=1)
        fig.update_yaxes(title_text='Violations', row=1, col=1)
        fig.update_yaxes(title_text='Violations', row=2, col=1)
        
        fig.update_layout(height=600, showlegend=False)
        
        return fig
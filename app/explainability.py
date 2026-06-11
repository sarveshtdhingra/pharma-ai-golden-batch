"""
Explainability Module
Provides insights into why recommendations are made using feature importance and correlations
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from app.utils import get_cpp_columns


class ExplainabilityEngine:
    """
    Provides explainability for batch quality predictions
    """
    
    def __init__(self, df):
        """
        Initialize explainability engine
        
        Parameters:
        df: Full batch DataFrame
        """
        
        self.df = df.copy()
        self.cpp_columns = get_cpp_columns()
        
        # Train predictive models
        self.impurity_model = None
        self.cycle_model = None
        self.yield_model = None
        
        self.impurity_importance = None
        self.cycle_importance = None
        self.yield_importance = None
        
        self._train_models()
    
    def _prepare_features(self):
        """
        Prepare feature matrix and scale
        
        Returns:
        tuple: X (features), scaler
        """
        
        X = self.df[self.cpp_columns].copy()
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        return X_scaled, scaler
    
    def _train_models(self):
        """
        Train predictive models for impurity, cycle time, and yield
        """
        
        X, _ = self._prepare_features()
        
        # Train impurity model
        self.impurity_model = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
        )
        self.impurity_model.fit(X, self.df['Total_Impurity'])
        self.impurity_importance = self.impurity_model.feature_importances_
        
        # Train cycle time model
        self.cycle_model = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
        )
        self.cycle_model.fit(X, self.df['Cycle_Time'])
        self.cycle_importance = self.cycle_model.feature_importances_
        
        # Train yield model
        self.yield_model = GradientBoostingRegressor(
            n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42
        )
        self.yield_model.fit(X, self.df['Yield'])
        self.yield_importance = self.yield_model.feature_importances_
    
    def get_feature_importance(self):
        """
        Get feature importance for all quality metrics
        
        Returns:
        DataFrame: Feature importance scores
        """
        
        importance_df = pd.DataFrame({
            'CPP': self.cpp_columns,
            'Impurity_Importance': self.impurity_importance,
            'CycleTime_Importance': self.cycle_importance,
            'Yield_Importance': self.yield_importance,
        })
        
        # Calculate weighted importance (50% impurity, 25% cycle, 25% yield)
        importance_df['Weighted_Importance'] = (
            0.50 * importance_df['Impurity_Importance'] +
            0.25 * importance_df['CycleTime_Importance'] +
            0.25 * importance_df['Yield_Importance']
        )
        
        importance_df = importance_df.sort_values('Weighted_Importance', ascending=False)
        
        return importance_df
    
    def get_correlation_matrix(self):
        """
        Get correlation matrix between CPPs and quality metrics
        
        Returns:
        DataFrame: Correlation matrix
        """
        
        analysis_df = self.df[self.cpp_columns + ['Total_Impurity', 'Cycle_Time', 'Yield']]
        correlation = analysis_df.corr()
        
        return correlation
    
    def get_cpp_insights(self, cpp_name):
        """
        Get detailed insights for a specific CPP
        
        Parameters:
        cpp_name: Name of CPP
        
        Returns:
        dict: Insights about the CPP
        """
        
        if cpp_name not in self.cpp_columns:
            return None
        
        # Get correlations
        corr_impurity = self.df[cpp_name].corr(self.df['Total_Impurity'])
        corr_cycle = self.df[cpp_name].corr(self.df['Cycle_Time'])
        corr_yield = self.df[cpp_name].corr(self.df['Yield'])
        
        # Get feature importance
        cpp_index = self.cpp_columns.index(cpp_name)
        impurity_imp = self.impurity_importance[cpp_index]
        cycle_imp = self.cycle_importance[cpp_index]
        yield_imp = self.yield_importance[cpp_index]
        
        # Generate insights
        insights = {
            'cpp': cpp_name,
            'correlation_impurity': corr_impurity,
            'correlation_cycle': corr_cycle,
            'correlation_yield': corr_yield,
            'importance_impurity': impurity_imp,
            'importance_cycle': cycle_imp,
            'importance_yield': yield_imp,
        }
        
        # Generate text insights
        text_insights = []
        
        if abs(corr_impurity) > 0.3:
            direction = "increases" if corr_impurity > 0 else "decreases"
            text_insights.append(
                f"{cpp_name} {direction} impurity levels (correlation: {corr_impurity:.3f})"
            )
        
        if abs(corr_cycle) > 0.3:
            direction = "increases" if corr_cycle > 0 else "decreases"
            text_insights.append(
                f"{cpp_name} {direction} cycle time (correlation: {corr_cycle:.3f})"
            )
        
        if abs(corr_yield) > 0.3:
            direction = "increases" if corr_yield > 0 else "decreases"
            text_insights.append(
                f"{cpp_name} {direction} product yield (correlation: {corr_yield:.3f})"
            )
        
        insights['text_insights'] = text_insights if text_insights else ["No strong correlations found"]
        
        return insights
    
    def get_batch_explanation(self, batch_id):
        """
        Explain why a batch has certain quality characteristics
        
        Parameters:
        batch_id: Batch ID to explain
        
        Returns:
        dict: Explanation of batch characteristics
        """
        
        batch = self.df[self.df['Batch_ID'] == batch_id]
        
        if batch.empty:
            return None
        
        batch_data = batch.iloc[0]
        
        X, scaler = self._prepare_features()
        batch_idx = self.df[self.df['Batch_ID'] == batch_id].index[0]
        batch_features = X[batch_idx:batch_idx+1]
        
        # Get predictions
        pred_impurity = self.impurity_model.predict(batch_features)[0]
        pred_cycle = self.cycle_model.predict(batch_features)[0]
        pred_yield = self.yield_model.predict(batch_features)[0]
        
        explanation = {
            'batch_id': batch_id,
            'actual_impurity': batch_data['Total_Impurity'],
            'predicted_impurity': pred_impurity,
            'actual_cycle_time': batch_data['Cycle_Time'],
            'predicted_cycle_time': pred_cycle,
            'actual_yield': batch_data['Yield'],
            'predicted_yield': pred_yield,
        }
        
        # Get contributing factors
        importance_df = self.get_feature_importance()
        top_factors = importance_df.head(5)
        
        explanation['top_factors'] = top_factors.to_dict('records')
        
        return explanation
    
    def get_quality_drivers(self, target='impurity'):
        """
        Get top drivers for a specific quality metric
        
        Parameters:
        target: 'impurity', 'cycle', or 'yield'
        
        Returns:
        DataFrame: Top driving CPPs for the target metric
        """
        
        importance_df = self.get_feature_importance()
        
        if target.lower() == 'impurity':
            col = 'Impurity_Importance'
        elif target.lower() == 'cycle':
            col = 'CycleTime_Importance'
        elif target.lower() == 'yield':
            col = 'Yield_Importance'
        else:
            col = 'Weighted_Importance'
        
        drivers = importance_df[['CPP', col]].sort_values(col, ascending=False)
        drivers.columns = ['CPP', 'Importance']
        
        return drivers


if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from dummy_data_generator import generate_realistic_pharma_batches
    
    df = generate_realistic_pharma_batches(n_batches=500)
    engine = ExplainabilityEngine(df)
    
    print("Feature Importance:")
    print(engine.get_feature_importance())
    
    print("\nCPP Insights (Reaction_Temperature):")
    print(engine.get_cpp_insights('Reaction_Temperature'))

    def _enhance_bar_chart(self, fig, chart_type, title, df_filtered=None):
        """Enhances bar chart with hover info and clickable data."""
        df_to_use = df_filtered if df_filtered is not None else self.df
import pandas as pd
import streamlit as st
import plotly.express as px

df = pd.read_csv("scores.csv")
df = df.replace("x", None)
df.rename(columns={'Unnamed: 5': 'Game Total', 'Unnamed: 10': 'Spirit Total', 'Unnamed: 11': 'Total Total'}, inplace=True)

df = df.dropna(subset=['Team Member']).sort_values(by='Total Total', ascending=False)

view_option = st.radio("Select View", ('Totals', 'Game Scores'))

if view_option == 'Totals':
    fig = px.bar(df, x='Team Member', y=['Game Total', 'Spirit Total'], title='Scores')
elif view_option == 'Game Scores':
    fig = px.bar(df, x='Team Member', y=['Free Throw', 'Putting', 'Beer Pong', 'Corn Hole'], title='Game Scores')

fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')

# Add a data table with emojis
df['Emoji'] = df.apply(lambda row: '🏆' if row['Total Total'] == df['Total Total'].max() else '🍪', axis=1)

for i, row in df.iterrows():
    fig.add_annotation(
        x=row['Team Member'],
        y=row['Total Total'] if view_option == 'Totals' else row['Game Total'],
        text=row['Emoji'],
        showarrow=False,
        yshift=10
    )

st.plotly_chart(fig, use_container_width=True)
st.dataframe(df[['Team Member', 'Game Total', 'Spirit Total', 'Total Total', 'Emoji']], use_container_width=True)
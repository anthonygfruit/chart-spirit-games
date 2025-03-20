import pandas as pd
import streamlit as st
import plotly.express as px

df = pd.read_csv("../../Downloads/scores.csv")
df = df.replace("x", None)
df.rename(columns={'Unnamed: 5': 'Game Total', 'Unnamed: 10': 'Spirit Total', 'Unnamed: 11': 'Total Total'}, inplace=True)

df = df.sort_values(by='Total Total', ascending=False)

view_option = st.radio("Select View", ('Totals', 'Game Scores'))

if view_option == 'Totals':
    fig = px.bar(df, x='Team Member', y=['Game Total', 'Spirit Total'], title='Scores')
elif view_option == 'Game Scores':
    fig = px.bar(df, x='Team Member', y=['Free Throw', 'Putting', 'Beer Pong', 'Corn Hole'], title='Game Scores')

fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')

# Add a data table with emojis
df['Emoji'] = df.apply(lambda row: '🏆' if row['Total Total'] == df['Total Total'].max() or row['Game Total'] == df['Game Total'].max() or row['Spirit Total'] == df['Spirit Total'].max() else '🍪', axis=1)
st.plotly_chart(fig, width=1200)
st.dataframe(df, width=1200)
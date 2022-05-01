#%%
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime, time
from PIL import Image
import json

from tensorboard import summary

weekday_name_dict = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun"
}

record_cols = ['study', 'sports', 'entertainment', 'spending', 'study_tar', 'sports_tar', 'entertainment_tar', 'spending_tar']
#record = pd.DataFrame(columns=record_cols)  # sample dataframe
#record.to_csv('daily_records.csv')
record = pd.read_csv('daily_records.csv', index_col=0, parse_dates=[0], date_parser=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d"))

# If there is no today's record entry in excel file, add one empty
if len(record) == 0 or record.index[-1] != pd.DatetimeIndex([datetime.date.today()]):
    record = record.append(pd.DataFrame([[0]*len(record_cols)], columns=record_cols, index=pd.DatetimeIndex([datetime.date.today()])))
    if len(record) > 1:
        record.iloc[-1, 4:] = record.iloc[-2, 4:]

# Navigate to "Edit Record" page if "Edit Now" button in home page is clicked
if 'home_to_edit' in st.session_state and 'current_page' in st.session_state and st.session_state['home_to_edit']:
    st.session_state['current_page'] = 'Edit Record'

# Navigate to "Home" page and update csv record if "Submit" button in edit page is clicked
if 'submit_record' in st.session_state and 'current_page' in st.session_state and st.session_state['submit_record']:
    st.session_state['current_page'] = 'Home'
    record.iloc[-1] = [
            st.session_state.study,
            st.session_state.sports,
            st.session_state.entertainment,
            st.session_state.spending,
            st.session_state.study_tar,
            st.session_state.sports_tar,
            st.session_state.entertainment_tar,
            st.session_state.spending_tar
            ]
    record.to_csv("./daily_records.csv")

# Sidebar to navigate through pages
current_page = st.sidebar.selectbox(label='Current Page', options=['Home', 'Edit Record', 'Habit Summary'], index=0, key='current_page')

if current_page == 'Home':
    with st.container():
        col1, col2 = st.columns([2, 1])
        col1.markdown('<font style="font-size:30px; color:lightpink"> Welcome </font>', True)
        col2.markdown(f'<font style="font-size:30px; color:lightpink"> {datetime.date.today().strftime("%d-%m-%Y")} \
            ({weekday_name_dict[datetime.date.today().weekday()]}) </font>', True)
    if sum(record.iloc[-1, :4]) == 0:
        st.markdown('<font style="font-size:30px"> You have not yet entered today\'s record!</font>', unsafe_allow_html=True)
        st.button("Edit Now", key="home_to_edit")
    else:
        st.markdown('<font style="font-size:30px"> Great! You have entered today\'s record! </font>', unsafe_allow_html=True)
        st.button("Edit Now", key="home_to_edit")
        with st.container():
            col1, col2, col3 = st.columns([6, 1, 5])
        # Plot productivity chart
            today_record_df = pd.DataFrame(record.iloc[-1].T)
            today_record_df.columns = ['Hour']
            today_record_df = today_record_df.drop(['spending', 'spending_tar'], axis=0)
            today_record_df['Actual/Target'] = ["Actual"]*(len(today_record_df)//2) + ["Target"]*(len(today_record_df)//2)
            today_record_df['category'] = list(today_record_df.index[:3])*2

            fig, ax = plt.subplots(1,1, figsize=(4,4))
            sns.barplot(data=today_record_df, y='category', x='Hour', hue='Actual/Target', palette=['skyblue', 'grey'], ax=ax)
            plt.ylabel("")

            productivity_diff = today_record_df.groupby(by='category', sort=False)['Hour'].apply(lambda x: x[0] - x[-1])
            color_map = []
            for i in productivity_diff.values:
                if i >= 0:
                    color_map += ['g']
                else:
                    color_map += ['r']

            for ytick, color in zip(ax.get_yticklabels(), color_map):
                ytick.set_color(color)

            col1.markdown('<font style="color:skyblue; font-size:20px"> Today\'s Productivity </font>', True)
            col1.pyplot(fig)
        # Daily spending metric
            spending_diff = (record.iloc[-1]["spending"] - record.iloc[-1]["spending_tar"])/record.iloc[-1]["spending_tar"]*100
            if spending_diff <= 0:
                col3.markdown(f'<font style="color:lightgreen; font-size:20px"> You have spent _**Less**_ than daily budget by _**{-spending_diff:.2f}%**_</font>', True)
                col3.markdown(f'<font style="color:lightgreen; font-size:50px; font-family: Arial"> &nbsp;&nbsp;*${record.iloc[-1]["spending"]}/{record.iloc[-1]["spending_tar"]}* </font>', True)
                st.snow()
            else:
                col3.markdown(f'<font style="color:red; font-size:20px"> You have spend _**More**_ than daily budget by _**{spending_diff:.2f}%**_</font>', True)
                col3.markdown(f'<font style="color:red; font-size:40px; font-family: Arial"> &nbsp;&nbsp;*${record.iloc[-1]["spending"]}/{record.iloc[-1]["spending_tar"]}* </font>', True)
                col3.image(Image.open("./images/sad_face.png").resize((180, 180)), use_column_width='auto')

if current_page == 'Edit Record':
    with st.container():
        col1, col2 = st.columns([2, 1])
        col1.markdown('<font style="font-size:30px; color:lightpink"> **Edit Today\'s Record** </font>', True)
        col2.markdown(f'<font style="font-size:30px; color:lightpink"> **{datetime.date.today().strftime("%d-%m-%Y")} ({weekday_name_dict[datetime.date.today().weekday()]})** </font>', True)
    st.markdown("----------------")


    col1, col2, col3 = st.columns(3)
    col2.markdown("**Actual Hour**")
    col3.markdown("**Target Hour**")
    with st.container():
        col1, col2, col3 = st.columns(3)
        for key in record_cols[:3]:
            col1.text_input("", value=key, disabled=True)
            col2.number_input("", value=record.iloc[-1][key], key=key, min_value=0.0, step=0.5)
            col3.number_input("", value=record.iloc[-1][f"{key}_tar"], key=f"{key}_tar", min_value=0.0, step=0.5)
    col2.markdown("**Actual Spending**")
    col3.markdown("**Target Spending**")
    with st.container():
        col1, col2, col3 = st.columns(3)
        col1.text_input("", value="spending ($)", disabled=True)
        col2.number_input("", value=record.iloc[-1]['spending'], key='spending', min_value=0.0, step=100.0)
        col3.number_input("", value=record.iloc[-1]['spending_tar'], key='spending_tar', min_value=0.0, step=100.0)
        submit_button = col1.button("Submit", key='submit_record')

if current_page == 'Habit Summary':
    with st.container():
        col1, col2 = st.columns([2, 1])
        col1.markdown('<font style="font-size:30px; color:lightpink"> Habit Summary </font>', True)
        col2.markdown(f'<font style="font-size:30px; color:lightpink"> {datetime.date.today().strftime("%d-%m-%Y")} \
            ({weekday_name_dict[datetime.date.today().weekday()]}) </font>', True)
        col1, col2, col3 = st.columns([1, 1, 1.3])
        col1.selectbox(label='Summary Period', options=[
            'Week-to-Date', 'Month-to-Date', 'Year-to-Date', 'Custom'
            ], key='summary_type')

        if st.session_state['summary_type'] == 'Week-to-Date':
            default_from = datetime.date.today() - datetime.timedelta(days=7)
        elif st.session_state['summary_type'] in ['Month-to-Date, Custome']:
            default_from = datetime.date.today() - datetime.timedelta(days=30)
        else:
            default_from = datetime.date.today() - datetime.timedelta(days=365)
        with st.container():
            col1, col2, col3 = st.columns([1, 1, 1.3])
            if st.session_state['summary_type'] == 'Custom':
                col1.date_input(label='From', value=default_from, key='from_date')
            else:
                col1.date_input(label='From', value=default_from, disabled=True, key='from_date')
            col2.date_input(label='To', value=datetime.date.today(), key='to_date')
        generate_summary = col1.button('Generate Summary')
        
        # Generate Summary
        if generate_summary:
            summary_df = record.loc[(np.datetime64(st.session_state['to_date']) >= record.index) & (record.index >= np.datetime64(st.session_state['from_date']))]

            # Productivity Summary
            summary_df['actual_total'] = summary_df.iloc[:, :3].sum(axis=1)  # Total Daily Actual Productivity 
            summary_df['target_total'] = summary_df.iloc[:, 4:7].sum(axis=1)  # Total Daily Target Productivity 
            # Plot productivity graph
            fig, ax = plt.subplots(1, 1, figsize=(12, 4))
            sns.lineplot(data=summary_df[['actual_total', 'target_total']], ax=ax)
            ax.set_xticks(summary_df.index[::len(summary_df)//10+1])
            ax.set_ylabel('Hour')
            st.markdown('<font style="color:skyblue; font-size:24px"> **Period Productivity Summary** </font>', True)
            st.pyplot(fig)

            # Productivity Summary by Category
            summary_by_cat = summary_df.T.loc[
                ['study', 'sports', 'entertainment', 'study_tar', 'sports_tar', 'entertainment_tar']
                ]
            summary_by_cat = pd.DataFrame(summary_by_cat.sum(axis=1), columns=['Hour'])
            summary_by_cat['category'] = ['study', 'sports', 'entertainment']*2
            summary_by_cat['Actual/Target'] = ['Actual']*3+['Target']*3
            # Plot productivity by category bar chart
            fig, ax = plt.subplots(1,1, figsize=(10,10))
            sns.barplot(data=summary_by_cat, y='category', x='Hour', hue='Actual/Target', palette=['skyblue', 'grey'], ax=ax)
            plt.ylabel("")

            productivity_diff = summary_by_cat.groupby(by='category', sort=False)['Hour'].apply(lambda x: x[0] - x[-1])
            color_map = []
            for i in productivity_diff.values:
                if i >= 0:
                    color_map += ['g']
                else:
                    color_map += ['r']

            for ytick, color in zip(ax.get_yticklabels(), color_map):
                ytick.set_color(color)
            
            st.markdown('<font style="color:skyblue; font-size:24px"> Period Productivity by Category </font>', True)
            st.pyplot(fig)

            # Spending Sumamry
            total_budget_diff = summary_df['spending_tar'].sum(axis=0) - summary_df['spending'].sum(axis=0)
            if total_budget_diff >= 0:
                st.markdown(f'<font style="color:green; font-size:24px"> **Period Budget Surplus**: ${total_budget_diff:.1f} </font>', True)
            else:
                st.markdown(f'<font style="color:red; font-size:24px"> **Period Budget Deficit**: ${total_budget_diff:.1f} </font>', True)
            # Plot spending graph
            fig, ax = plt.subplots(1, 1, figsize=(12, 4))
            sns.lineplot(data=summary_df[['spending', 'spending_tar']], ax=ax)
            ax.set_xticks(summary_df.index[::len(summary_df)//10+1])
            ax.set_ylabel('Money spent ($)')
            st.markdown('<font style="font-size:24px"> **Spending Behavior** </font>', True)
            st.pyplot(fig)



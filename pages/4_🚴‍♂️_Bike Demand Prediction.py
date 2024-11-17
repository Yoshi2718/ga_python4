# import libraries
import streamlit as st
import pandas as pd
import joblib
from datetime import datetime, timedelta
import numpy as np

# Load data and model
data_cleaned = pd.read_csv('data/data_cleaned.csv')
catboost_model = joblib.load('data/trained_catboost_model.pkl')

# Define the function that returns the season based on the selected date
def get_season(date):
    month = date.month
    # Define season based on the month and day
    if (month >= 3 and month <= 5):  # March to May
        return "Spring"
    elif (month >= 6 and month <= 8):  # June to August
        return "Summer"
    elif (month >= 9 and month <= 11):  # September to November
        return "Autumn"
    else:  # December to February
        return "Winter"
    
# Function to generate a list of times at 15-minute intervals
def generate_time_options():
    times = []
    current_time = datetime.strptime("00:00", "%H:%M")
    while current_time < datetime.strptime("23:45", "%H:%M"):
        times.append(current_time.strftime("%H:%M"))
        current_time += timedelta(minutes=15)
    return times

# Define the function which will make the prediction using the data which the user inputs 
def user_input_features():
    st.header("Prediction Inputs")
    
    st.subheader("📅 Calender Features")

    # Date and Time Picker
    date = st.date_input("Select Date", value = datetime.today(), min_value=datetime(2011, 1, 1))

    # Dropdown for selecting time in 15-minute intervals
    time_options = generate_time_options()
    selected_time = st.selectbox("Select Time", time_options, index=time_options.index("12:00"))  # Default to 12:00

    # Combine the selected date and time into a single datetime object
    selected_datetime = datetime.combine(date, datetime.strptime(selected_time, "%H:%M").time())
    
    # Extract season from selected date
    season = get_season(selected_datetime)
    season_mapping = {"Winter": 1, "Spring": 2, 
                      "Summer": 3, "Autumn": 4}
    season_encoded = season_mapping[season]

    # Display the selected season
    st.write(f"Selected Season: **{season}**")

    # Extract month from selected date
    mnth = selected_datetime.month

    # Extract hour from selected date
    hr = selected_datetime.hour

    # Extract day of the week from selected date
    weekday = selected_datetime.strftime("%A")  # Full day name, e.g., "Monday"

    # Display the selected day of the week
    st.write(f"Selected Day of the Week: **{weekday}**")
    weekday_mapping = {
        "Sunday": 0,
        "Monday": 1,
        "Tuesday": 2,
        "Wednesday": 3,
        "Thursday": 4,
        "Friday": 5,
        "Saturday": 6
    }
    weekday_encoded = weekday_mapping.get(weekday)

    # Determine if it is a working day
    if weekday in ["Saturday", "Sunday"]:
        workingday = 0  # Weekend, not a working day
    else:
        workingday = 1  # Weekday, likely a working day

    #total number of hours, months, weeks and seasons
    h = 24 
    m = 12
    w = 7
    s = 4

    hr_sin = np.sin(2 * np.pi * hr / h)
    hr_cos = np.cos(2 * np.pi * hr / h)
    mnth_sin = np.sin(2 * np.pi * mnth / m)
    mnth_cos = np.cos(2 * np.pi * mnth / m)
    weekday_sin  = np.sin(2 * np.pi * weekday_encoded / w)
    weekday_cos = np.cos(2 * np.pi * weekday_encoded / w)
    season_sin = np.sin(2 * np.pi * season_encoded / s)
    season_cos = np.cos(2 * np.pi * season_encoded / s)

    # Holiday and Working Day with "Yes" or "No" options
    holiday = st.selectbox("Is it a holiday?", ["No", "Yes"])
    holiday = 1 if holiday == "Yes" else 0

    st.subheader("☀️ Weather Features")

    # Weather situation selection with descriptive text
    weathersit = st.selectbox("Weather Situation", 
                              ["☀️ Clear", "🌥️ Cloudy/Mist", "🌦️ Light Rain/Snow", "🌧️ Heavy Rain/Snow"])
    weathersit_mapping = {"☀️ Clear": [1, 0, 0, 0], "🌥️ Cloudy/Mist": [0, 1, 0, 0], 
                            "🌦️ Light Rain/Snow": [0, 0, 1, 0], "🌧️ Heavy Rain/Snow": [0, 0, 0, 1]}

    # Continuous variables
    temp = st.slider("Temperature (°C)", min_value=float(-20), max_value=float(50), value=20.0, step=1.0)
    hum = st.slider("Humidity (%)", float(data_cleaned['hum'].min()), float(data_cleaned['hum'].max()), 50.0, step=1.0)
    windspeed = st.slider("Wind Speed (m/s)", float(data_cleaned['windspeed'].min()), float(60), 10.0, step=1.0)


    # Combine all features, including mapped flags for categorical variables
    features = {
        "mnth": mnth,
        "hr": hr,
        "holiday": holiday,
        "workingday": workingday,
        "temp": temp,
        "hum": hum,
        "windspeed": windspeed,
        # Categorical flags (one-hot encoded)
        "season": season_encoded,
        "weekday": weekday_encoded,
        "weathersit_1": weathersit_mapping[weathersit][0],
        "weathersit_2": weathersit_mapping[weathersit][1],
        "weathersit_3": weathersit_mapping[weathersit][2],
        "weathersit_4": weathersit_mapping[weathersit][3],
        "hr_sin": hr_sin,
        "hr_cos": hr_cos,
        "mnth_sin": mnth_sin,
        "mnth_cos": mnth_cos,
        "weekday_sin": weekday_sin,
        "weekday_cos": weekday_cos,
        "season_sin": season_sin,
        "season_cos": season_cos
    }
    return features

# Prediction function
def predict_demand(features):
    # Convert features dictionary to DataFrame for model compatibility
    input_df = pd.DataFrame([features])
    
    # Predict using the random forest model
    prediction = catboost_model.predict(input_df)[0]
    if prediction <0:
        prediction=0
    return prediction

# Define the main function for the "Modeling" page
def main():
    # Get user input features
    features = user_input_features()
    
    st.header("Check Bike Demand")

    # Display prediction result on button click
    if st.button("Predict Bike Demand"):
        prediction = predict_demand(features)
        
        # Display prediction in a visually appealing format
        st.markdown(
            f"""
            <div style="background-color:#f5f5f5; padding:20px; border-radius:10px; text-align:center;">
                <h2 style="color:#4CAF50; font-weight:bold;">📈 Predicted Bike Demand</h2>
                <p style="font-size:28px; color:#1E90FF; font-weight:bold;">
                    {int(prediction):,} rentals 🚴‍♂️
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# Check if the script is being run directly
if __name__ == "__main__":
    main()
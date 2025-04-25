# API Documentation for Server Monitoring Bot
This is the API documentation for a Telegram bot designed to monitor server availability using periodic ping tests. The bot allows users to configure their monitoring settings, add and manage server links, and control the frequency of ping tests.

## Requirements
- Python 3.7 or later
- Required packages: aiogram, requests, aiosqlite
- A working Telegram bot token

## Bot Commands
`/start`
- Description: Initializes the bot and prompts the user to select a ping frequency for server monitoring.
- Usage: /start
- Response: Sends a message with options for selecting a ping interval.

`/timeout`
- Description: Allows the user to change the ping interval for server monitoring.
- Usage: /timeout
- Response: Displays a list of available ping intervals for the user to select.

`/add_server`
- Description: Allows the user to add a new server link for monitoring.
- Usage: /add_server
- Response: Prompts the user to input a server URL.

`/add_database`
- Description: Allows the user to add a database server link for monitoring.
- Usage: /add_database
- Response: Prompts the user to input a database URL.

`/start_ping`
- Description: Starts the ping test for the user's added servers.
- Usage: /start_ping
- Response: Starts pinging the servers at the configured interval.

`/break_ping`
- Description: Pauses the ongoing ping test.
- Usage: /break_ping
- Response: Notifies the user that the ping test has been paused.

`/remove_ping`
- Description: Allows the user to remove a server from the monitoring list.
- Usage: /remove_ping
- Response: Prompts the user to select a server to remove from the list.

`/fast_ping`
- Description: Runs an immediate ping test on all added servers.
- Usage: /fast_ping
- Response: Provides the status of each server with a quick ping.

## Key Functionalities
### Server Ping Monitoring
- The bot monitors the availability of servers by periodically sending HTTP requests.
- Users can add both regular web servers and database servers.
- The ping interval can be customized from 5 minutes to 24 hours.

### Ping Interval Options
The bot supports the following ping intervals:
- 5 minutes: Pings every 5 minutes.
- 30 minutes: Pings every 30 minutes.
- 1 hour: Pings every 1 hour.
- 3 hours: Pings every 3 hours.
- 12 hours: Pings every 12 hours.
- 24 hours: Pings every 24 hours.

### Server Link Management
Users can add and remove server links for monitoring. The bot stores the server links in a database, and each user can have a defined limit for the number of servers they can monitor.

### Data Storage
The bot uses an SQLite database to store user information and server links. The database includes two main tables:

- User: Stores user data such as ID, bot timeout, and link limit.
- Server: Stores server information such as the user ID, server link, and server type.

### Bot Responses
The bot provides feedback messages for user actions such as starting or stopping the ping test, adding servers, and changing settings. It also sends the status of each server being monitored, indicating whether the server is online or offline.

## Database Schema
The bot uses SQLite for data storage. The schema is as follows:

`User` Table

| Column | Type | Description |
| ------ | ---- | ----------- |
| id | INTEGER | The unique user ID. |
| link\_limit | INTEGER | The maximum number of server links a user can add. |
| enable | BOOLEAN | Indicates whether the user has active ping monitoring. |
| bot\_timeout | INTEGER | The interval for pinging the servers in seconds. |

`Server` Table

| Column | Type | Description |
| ------ | ---- | ----------- |
| user\_id | INTEGER | The user ID associated with the server. |
| link | TEXT | The server link (URL). |
| type | TEXT | The type of server (e.g., "web" or "database"). |


### Callback Queries
The bot supports callback queries to set the ping interval. These queries are triggered when a user selects a ping interval.

`IntervalCallback`
- Description: Handles user selection of a ping interval.
- Callback Data: The name of the selected interval (e.g., "5 минут", "1 час").
- Action: Updates the user's ping interval setting in the database and sends a confirmation message.

### Error Handling
The bot uses `try-except` blocks to handle exceptions such as network errors and database issues. If an error occurs during server pinging or database operations, the bot attempts to handle the error gracefully and inform the user.

### Example Usage (you can try: `@ping_my_server_online_bot`)
1. Start the Bot:
   - Send /start to initiate the bot and choose a ping interval.

2. Add a Server:

   - Send /add_server to add a new server link for monitoring.

3. Start Ping Test:

   - Send /start_ping to start the ping test based on the selected interval.

4. Stop Ping Test:

   - Send /break_ping to pause the ongoing ping test.

5. Remove a Server:

   - Send /remove_ping to remove a server from the monitoring list.

This bot helps users monitor the status of their servers and ensures they receive timely updates on their availability.

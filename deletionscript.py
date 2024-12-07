import click
import requests
from datetime import datetime, timezone

# Hardcoded ThingsBoard URL and credentials
TB_URL = ""
USERNAME = "" 
PASSWORD = ""

def login():
    """Authenticate and get JWT token from ThingsBoard."""
    login_url = f"{TB_URL}/api/auth/login"
    login_payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    response = requests.post(login_url, json=login_payload)
    if response.status_code == 200:
        return response.json().get("token")
    else:
        raise Exception(f"Login failed: {response.json()}")

def get_device_id(token, device_name):
    """Fetch device UUID using its name."""
    headers = {
        "Content-Type": "application/json",
        "X-Authorization": f"Bearer {token}"
    }
    search_url = f"{TB_URL}/api/tenant/devices?deviceName={device_name}"
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        devices = response.json()
        if devices and devices.get("id") and devices["id"].get("id"):
            return devices["id"]["id"]  # Return the UUID
        else:
            raise ValueError(f"No device found with name: {device_name}")
    else:
        raise Exception(f"Failed to fetch device ID: {response.json()}")

def convert_to_epoch(date_str, time_str=None):
    """
    Convert date and time strings to epoch milliseconds.
    Supports date format: DD/MM/YYYY and time format: HH:MM.
    """
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        if time_str:
            hours, minutes = map(int, time_str.split(':'))
            dt = dt.replace(hour=hours, minute=minutes)
        utc_dt = dt.astimezone(timezone.utc)
        return int(utc_dt.timestamp() * 1000)
    except ValueError as e:
        raise ValueError(f"Invalid date/time format: {e}")

@click.command()
@click.option('--device-name', required=True, help='Name of the device to delete telemetry from.')
@click.option('--start-date', required=True, help='Start date for deletion (DD/MM/YYYY).')
@click.option('--end-date', required=True, help='End date for deletion (DD/MM/YYYY).')
@click.option('--start-time', default='00:00', show_default=True, help='Start time for deletion (HH:MM, 24-hour format).')
@click.option('--end-time', default='23:59', show_default=True, help='End time for deletion (HH:MM, 24-hour format).')
def delete_telemetry(device_name, start_date, end_date, start_time, end_time):
    """
    Delete telemetry data for a device within a specific time range.
    
    Example usage:
    python script.py --device-name 20090231 --start-date 03/06/2021 --end-date 23/06/2021
    """
    try:
        # Authenticate and get token
        token = login()

        # Fetch device UUID
        device_id = get_device_id(token, device_name)

        # Convert times to epoch
        start_epoch = convert_to_epoch(start_date, start_time)
        end_epoch = convert_to_epoch(end_date, end_time)

        # Prepare API request
        headers = {
            "Content-Type": "application/json",
            "X-Authorization": f"Bearer {token}"
        }
        delete_url = f"{TB_URL}/api/plugins/telemetry/DEVICE/{device_id}/timeseries/delete"
        params = {
            "startTs": start_epoch,
            "endTs": end_epoch,
            "rewriteLatestIfDeleted": True
        }

        # Send delete request
        response = requests.delete(delete_url, headers=headers, params=params)
        if response.status_code == 200:
            click.echo(click.style(f"Telemetry data for device '{device_name}' deleted successfully.", fg='green'))
            click.echo(f"Deletion range: {datetime.fromtimestamp(start_epoch/1000, tz=timezone.utc)} to {datetime.fromtimestamp(end_epoch/1000, tz=timezone.utc)}")
        else:
            click.echo(click.style(f"Failed to delete telemetry data: {response.status_code}, {response.text}", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))

if __name__ == '__main__':
    delete_telemetry()
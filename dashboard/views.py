from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import csv
from .models import *
from .forms import SessionForm
import subprocess
import sys
import os
from datetime import datetime, time

SCRIPTS = {
    "sample": "scripts/sample_script.py",
    "Temperature": "scripts/Temp.py",
    "Stirrer": "scripts/stirrer.py",
}

def home(request):
    return render(request, 'dashboard/home.html', {
        'scripts': SCRIPTS,
        'sessions': Session.objects.all()
    })

def session_list(request):
    sessions = Session.objects.order_by('-created_at')
    return render(request, 'dashboard/sessions.html', {'sessions': sessions})

def exponential_moving_average(data, alpha=0.1):
    ema = [data[0]]
    for value in data[1:]:
        ema.append(alpha * value + (1 - alpha) * ema[-1])
    return ema

def session_detail(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    temperature_logs = session.temperature_logs.all().order_by('-timestamp')
    script_logs = session.scriptlog_set.all().order_by('-timestamp')

    log_files = []
    selected_file = request.GET.get("log_file")
    start_time_str = request.GET.get("start_time")
    end_time_str = request.GET.get("end_time")
    start_time = None
    end_time = None

    filtered_times = []
    filtered_weights = []

    log_folder_path = r"C:\Users\sequestra FlexCo\Desktop\Graphs\Trials_0704"

    if os.path.exists(log_folder_path):
        log_files = [
            f for f in os.listdir(log_folder_path)
            if f.endswith(".log") or f.endswith(".txt") or f.endswith(".csv")
        ]

        if selected_file and selected_file in log_files and start_time_str and end_time_str:
            file_path = os.path.join(log_folder_path, selected_file)

            try:
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()
            except ValueError:
                start_time = end_time = None

            if os.path.exists(file_path) and start_time and end_time:
                raw_times = []
                raw_weights = []

                with open(file_path, "r") as f:
                    for line in f:
                        try:
                            line = line.strip().replace(" kg", "")
                            t_str, val_str = line.split(",", 1)
                            t_obj = datetime.strptime(t_str.strip(), "%H:%M:%S").time()
                            if start_time <= t_obj <= end_time:
                                raw_times.append(datetime.strptime(t_str.strip(), "%H:%M:%S"))
                                raw_weights.append(float(val_str.strip().replace(",", ".")))
                        except:
                            continue

                # Noise filtering
                neighbor_size = 20
                for i in range(len(raw_weights)):
                    start = max(0, i - neighbor_size)
                    end = min(len(raw_weights), i + neighbor_size + 1)
                    window = raw_weights[start:i] + raw_weights[i+1:end]

                    if not window:
                        continue

                    avg_neighbors = sum(window) / len(window)
                    current_val = raw_weights[i]

                    if avg_neighbors == 0:
                        is_within_range = current_val == 0
                    else:
                        is_within_range = abs(current_val - avg_neighbors) / avg_neighbors <= 0.1

                    if is_within_range:
                        filtered_times.append(raw_times[i])
                        filtered_weights.append(current_val)

    smoothed_weights = exponential_moving_average(filtered_weights) if filtered_weights else []

    return render(request, 'dashboard/session_detail.html', {
        'session': session,
        'temperature_logs': temperature_logs,
        'script_logs': script_logs,
        'log_files': log_files,
        'selected_file': selected_file,
        'start_time': start_time_str,
        'end_time': end_time_str,
        'weighing_labels': [t.strftime("%H:%M:%S") for t in filtered_times],
        'weighing_values': smoothed_weights,
    })

def activate_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    if session.status != 'active':
        return redirect('session_detail', session_id=session.id)

    for key, script_path in SCRIPTS.items():
        if not os.path.isfile(script_path):
            ScriptLog.objects.create(
                script_name=key,
                output='',
                error='Script not found.',
                session=session
            )
            continue

        try:
            # Run the script and capture output
            process = subprocess.Popen(
                [sys.executable, script_path, str(session.id)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            # Log output and error
            ScriptLog.objects.create(
                script_name=os.path.basename(script_path),
                output=stdout,
                error=stderr,
                session=session
            )

        except Exception as e:
            ScriptLog.objects.create(
                script_name=os.path.basename(script_path),
                output='',
                error=str(e),
                session=session
            )

    return redirect('session_detail', session_id=session.id)

def end_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    session.status = 'ended'
    session.save()
    return redirect('session_detail', session_id=session.id)

def download_session_csv(request, session_id):
    session = Session.objects.get(id=session_id)
    logs = session.temperature_logs.order_by('timestamp')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{session.name}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Temperature (°C)'])
    for log in logs:
        writer.writerow([log.timestamp, log.temperature])
    return response

def session_chart_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    return render(request, 'dashboard/session_chart.html', {'session': session})

def session_chart_data(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    logs = list(reversed(session.temperature_logs.order_by('-timestamp')[:60]))

    data = {
        'labels': [log.timestamp.strftime('%H:%M:%S') for log in logs],
        'values': [log.temperature for log in logs]
    }
    return JsonResponse(data)

def create_session(request):
    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save()
            return redirect('session_detail', session_id=session.id)
    else:
        form = SessionForm()

    return render(request, 'dashboard/create_session.html', {'form': form})

def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    if request.method == 'POST':
        session_name = session.name
        session.delete()
        messages.success(request, f"Session '{session_name}' deleted.")
        return redirect('session_list')

    return render(request, 'dashboard/delete_session_confirm.html', {'session': session})

@csrf_exempt  # or use {% csrf_token %} in form
def set_rpm(request, session_id):
    if request.method == 'POST':
        try:
            new_rpm = int(request.POST.get('rpm'))
            session = Session.objects.get(id=session_id)
            new_rpm = max(100, min(new_rpm, 1500))  # Enforce range
            session.rpm = new_rpm
            session.save()
            return JsonResponse({'status': 'success', 'rpm': new_rpm})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
# ---------- Stirrer Views ----------

def stirrer_chart_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    return render(request, 'dashboard/stirrer_chart.html', {
        'session': session,
        'title': 'Stirrer RPM',
        'emoji': '🌀',
        'unit': 'RPM',
        'data_url': 'stirrer_chart_data'  # ← THIS was missing
    })

def stirrer_chart_data(request, session_id):
    logs = StirrerLog.objects.filter(session_id=session_id).order_by('-timestamp')[:100]
    logs = reversed(logs)
    data = {
        'labels': [log.timestamp.strftime('%H:%M:%S') for log in logs],
        'values': [log.rpm for log in logs]
    }
    return JsonResponse(data)

def download_stirrer_csv(request, session_id):
    logs = StirrerLog.objects.filter(session_id=session_id).order_by('timestamp')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stirrer_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'RPM'])
    for log in logs:
        writer.writerow([log.timestamp, log.rpm])

    return response

def list_files_view(request):
    directory = r"C:\Users\Siddarth Shankar\Desktop\Scale_Readings"
    
    try:
        files = os.listdir(directory)
        files = [f for f in files if os.path.isfile(os.path.join(directory, f))]
    except FileNotFoundError:
        files = []

    return render(request, 'dashboard/file_list.html', {'files': files})

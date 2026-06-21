import os
from datetime import date, datetime
from urllib.parse import quote
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from config import Config

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

API = 'https://xbanjubmkjqgryoiridz.supabase.co/rest/v1'
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYW5qdWJta2pxZ3J5b2lyaWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODIwODEsImV4cCI6MjA5NzU1ODA4MX0.uCy1x-clCRbCirv2c2rigM--z6SAJcvOf6GRskT-XCs',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhiYW5qdWJta2pxZ3J5b2lyaWR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE5ODIwODEsImV4cCI6MjA5NzU1ODA4MX0.uCy1x-clCRbCirv2c2rigM--z6SAJcvOf6GRskT-XCs',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

def supabase_get(table, params=None, count=False):
    h = dict(HEADERS)
    if count:
        h['Prefer'] = 'count=exact'
    r = requests.get(f'{API}/{table}', headers=h, params=params or {}, timeout=15)
    r.raise_for_status()
    if count:
        return r.json(), int(r.headers.get('content-range', '0-0/0').split('/')[1])
    return r.json()

def supabase_post(table, data, params=None):
    r = requests.post(f'{API}/{table}', headers=HEADERS, params=params or {}, json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def supabase_patch(table, data, id_val, id_col='id'):
    r = requests.patch(f'{API}/{table}?{id_col}=eq.{quote(str(id_val))}', headers=HEADERS, json=data, timeout=15)
    r.raise_for_status()
    return r.json()

def supabase_delete(table, id_val, id_col='id'):
    r = requests.delete(f'{API}/{table}?{id_col}=eq.{quote(str(id_val))}', headers={k:v for k,v in HEADERS.items() if k != 'Content-Type'}, timeout=15)
    r.raise_for_status()

def fmt_name(row, first='first_name', last='last_name'):
    return f"{row.get(first,'')} {row.get(last,'')}".strip()

def fmt_date(d):
    if not d:
        return '-'
    try:
        dt = datetime.fromisoformat(d.replace('Z','+00:00'))
        return dt.strftime('%b %d, %Y')
    except:
        return d[:10]

def fmt_time(t):
    if not t:
        return '-'
    return t[:5]

@app.context_processor
def inject_globals():
    return {'fmt_name': fmt_name, 'fmt_date': fmt_date, 'fmt_time': fmt_time, 'today': date.today().isoformat()}

@app.route('/')
def index():
    counts = {}
    for tbl in ['customers', 'dogs', 'walkers', 'walks', 'payments']:
        r, c = supabase_get(tbl, {'select': 'id', 'limit': '1'}, count=True)
        counts[tbl] = c
    recent = supabase_get('walks', {
        'select': '*,dogs(dog_name,customer_id),walkers(first_name,last_name)',
        'order': 'walk_date.desc',
        'limit': '10'
    })
    for w in recent:
        w['dog_name'] = w.get('dogs', {}).get('dog_name', '') if w.get('dogs') else ''
        w['walker_name'] = fmt_name(w.get('walkers', {})) if w.get('walkers') else ''
    return render_template('index.html', **counts, recent_walks=recent)

@app.route('/customers')
def list_customers():
    data = supabase_get('customers', {'order': 'last_name.asc'})
    return render_template('customers.html', customers=data, editing=None, form={})

@app.route('/customers/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        supabase_post('customers', {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form.get('email',''),
            'phone': request.form.get('phone',''),
            'address': request.form.get('address',''),
            'city': request.form.get('city',''),
            'emergency_contact': request.form.get('emergency_contact',''),
            'notes': request.form.get('notes','')
        })
        flash('Customer added', 'success')
        return redirect(url_for('list_customers'))
    return render_template('customers.html', customers=supabase_get('customers', {'order': 'last_name.asc'}), editing='new', form={})

@app.route('/customers/<id>/edit', methods=['GET', 'POST'])
def edit_customer(id):
    if request.method == 'POST':
        supabase_patch('customers', {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form.get('email',''),
            'phone': request.form.get('phone',''),
            'address': request.form.get('address',''),
            'city': request.form.get('city',''),
            'emergency_contact': request.form.get('emergency_contact',''),
            'notes': request.form.get('notes','')
        }, id)
        flash('Customer updated', 'success')
        return redirect(url_for('list_customers'))
    c = supabase_get('customers', {'id': f'eq.{id}'})[0]
    return render_template('customers.html', customers=supabase_get('customers', {'order': 'last_name.asc'}), editing=id, form=c)

@app.route('/customers/<id>/delete', methods=['POST'])
def delete_customer(id):
    supabase_delete('customers', id)
    flash('Customer deleted', 'success')
    return redirect(url_for('list_customers'))

@app.route('/dogs')
def list_dogs():
    data = supabase_get('dogs', {
        'select': '*,customers(first_name,last_name)',
        'order': 'dog_name.asc'
    })
    customers = supabase_get('customers', {'order': 'last_name.asc'})
    return render_template('dogs.html', dogs=data, customers=customers, editing=None, form={})

@app.route('/dogs/add', methods=['GET', 'POST'])
def add_dog():
    if request.method == 'POST':
        supabase_post('dogs', {
            'dog_name': request.form['dog_name'],
            'customer_id': request.form['customer_id'],
            'breed': request.form.get('breed',''),
            'age': request.form.get('age'),
            'weight': request.form.get('weight'),
            'temperament': request.form.get('temperament',''),
            'special_needs': request.form.get('special_needs','')
        })
        flash('Dog added', 'success')
        return redirect(url_for('list_dogs'))
    return render_template('dogs.html',
        dogs=supabase_get('dogs', {'select': '*,customers(first_name,last_name)', 'order': 'dog_name.asc'}),
        customers=supabase_get('customers', {'order': 'last_name.asc'}),
        editing='new', form={})

@app.route('/dogs/<id>/edit', methods=['GET', 'POST'])
def edit_dog(id):
    if request.method == 'POST':
        supabase_patch('dogs', {
            'dog_name': request.form['dog_name'],
            'customer_id': request.form['customer_id'],
            'breed': request.form.get('breed',''),
            'age': request.form.get('age'),
            'weight': request.form.get('weight'),
            'temperament': request.form.get('temperament',''),
            'special_needs': request.form.get('special_needs','')
        }, id)
        flash('Dog updated', 'success')
        return redirect(url_for('list_dogs'))
    d = supabase_get('dogs', {'id': f'eq.{id}'})[0]
    return render_template('dogs.html',
        dogs=supabase_get('dogs', {'select': '*,customers(first_name,last_name)', 'order': 'dog_name.asc'}),
        customers=supabase_get('customers', {'order': 'last_name.asc'}),
        editing=id, form=d)

@app.route('/dogs/<id>/delete', methods=['POST'])
def delete_dog(id):
    supabase_delete('dogs', id)
    flash('Dog deleted', 'success')
    return redirect(url_for('list_dogs'))

@app.route('/walkers')
def list_walkers():
    data = supabase_get('walkers', {'order': 'last_name.asc'})
    return render_template('walkers.html', walkers=data, editing=None, form={})

@app.route('/walkers/add', methods=['GET', 'POST'])
def add_walker():
    if request.method == 'POST':
        supabase_post('walkers', {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form.get('email',''),
            'phone': request.form.get('phone',''),
            'availability': request.form.get('availability',''),
            'max_dogs': request.form.get('max_dogs')
        })
        flash('Walker added', 'success')
        return redirect(url_for('list_walkers'))
    return render_template('walkers.html', walkers=supabase_get('walkers', {'order': 'last_name.asc'}), editing='new', form={})

@app.route('/walkers/<id>/edit', methods=['GET', 'POST'])
def edit_walker(id):
    if request.method == 'POST':
        supabase_patch('walkers', {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'email': request.form.get('email',''),
            'phone': request.form.get('phone',''),
            'availability': request.form.get('availability',''),
            'max_dogs': request.form.get('max_dogs')
        }, id)
        flash('Walker updated', 'success')
        return redirect(url_for('list_walkers'))
    w = supabase_get('walkers', {'id': f'eq.{id}'})[0]
    return render_template('walkers.html', walkers=supabase_get('walkers', {'order': 'last_name.asc'}), editing=id, form=w)

@app.route('/walkers/<id>/delete', methods=['POST'])
def delete_walker(id):
    supabase_delete('walkers', id)
    flash('Walker deleted', 'success')
    return redirect(url_for('list_walkers'))

@app.route('/walks')
def list_walks():
    data = supabase_get('walks', {
        'select': '*,dogs(dog_name,customer_id(first_name,last_name)),walkers(first_name,last_name)',
        'order': 'walk_date.desc'
    })
    dogs = supabase_get('dogs', {
        'select': '*,customers(first_name,last_name)',
        'order': 'dog_name.asc'
    })
    walkers = supabase_get('walkers', {'order': 'last_name.asc'})
    for w in data:
        w['dog_name'] = w.get('dogs', {}).get('dog_name','') if w.get('dogs') else ''
        cust = w.get('dogs', {}).get('customer_id', {}) if w.get('dogs') else {}
        w['customer_name'] = fmt_name(cust) if cust else ''
        w['walker_name'] = fmt_name(w.get('walkers', {})) if w.get('walkers') else ''
    return render_template('walks.html', walks=data, dogs=dogs, walkers=walkers, editing=None, form={})

@app.route('/walks/add', methods=['GET', 'POST'])
def add_walk():
    if request.method == 'POST':
        supabase_post('walks', {
            'dog_id': request.form['dog_id'],
            'walker_id': request.form['walker_id'],
            'walk_date': request.form['walk_date'],
            'duration': request.form.get('duration'),
            'status': request.form.get('status','scheduled'),
            'fee': request.form.get('fee'),
            'notes': request.form.get('notes','')
        })
        flash('Walk scheduled', 'success')
        return redirect(url_for('list_walks'))
    return render_template('walks.html',
        walks=supabase_get('walks', {
            'select': '*,dogs(dog_name,customer_id(first_name,last_name)),walkers(first_name,last_name)',
            'order': 'walk_date.desc'
        }),
        dogs=supabase_get('dogs', {'select': '*,customers(first_name,last_name)', 'order': 'dog_name.asc'}),
        walkers=supabase_get('walkers', {'order': 'last_name.asc'}),
        editing='new', form={})

@app.route('/walks/<id>/edit', methods=['GET', 'POST'])
def edit_walk(id):
    if request.method == 'POST':
        supabase_patch('walks', {
            'dog_id': request.form['dog_id'],
            'walker_id': request.form['walker_id'],
            'walk_date': request.form['walk_date'],
            'duration': request.form.get('duration'),
            'status': request.form.get('status','scheduled'),
            'fee': request.form.get('fee'),
            'notes': request.form.get('notes','')
        }, id)
        flash('Walk updated', 'success')
        return redirect(url_for('list_walks'))
    w = supabase_get('walks', {'id': f'eq.{id}'})[0]
    return render_template('walks.html',
        walks=supabase_get('walks', {
            'select': '*,dogs(dog_name,customer_id(first_name,last_name)),walkers(first_name,last_name)',
            'order': 'walk_date.desc'
        }),
        dogs=supabase_get('dogs', {'select': '*,customers(first_name,last_name)', 'order': 'dog_name.asc'}),
        walkers=supabase_get('walkers', {'order': 'last_name.asc'}),
        editing=id, form=w)

@app.route('/walks/<id>/delete', methods=['POST'])
def delete_walk(id):
    supabase_delete('walks', id)
    flash('Walk deleted', 'success')
    return redirect(url_for('list_walks'))

@app.route('/payments')
def list_payments():
    data = supabase_get('payments', {
        'select': '*,customers(first_name,last_name),walks(walk_date,dog_id(dog_name))',
        'order': 'payment_date.desc'
    })
    customers = supabase_get('customers', {'order': 'last_name.asc'})
    walks = supabase_get('walks', {
        'select': '*,dogs(dog_name)',
        'order': 'walk_date.desc'
    })
    for p in data:
        p['customer_name'] = fmt_name(p.get('customers', {})) if p.get('customers') else ''
        p['dog_name'] = p.get('walks', {}).get('dog_id', {}).get('dog_name','') if p.get('walks') and p['walks'].get('dog_id') else ''
        p['walk_date'] = p.get('walks', {}).get('walk_date','') if p.get('walks') else ''
    return render_template('payments.html', payments=data, customers=customers, walks=walks, editing=None, form={})

@app.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    if request.method == 'POST':
        supabase_post('payments', {
            'customer_id': request.form['customer_id'],
            'walk_id': request.form.get('walk_id') or None,
            'amount': request.form['amount'],
            'payment_date': request.form['payment_date'],
            'payment_method': request.form.get('payment_method','')
        })
        flash('Payment recorded', 'success')
        return redirect(url_for('list_payments'))
    return render_template('payments.html',
        payments=supabase_get('payments', {'select': '*,customers(first_name,last_name),walks(walk_date,dog_id(dog_name))', 'order': 'payment_date.desc'}),
        customers=supabase_get('customers', {'order': 'last_name.asc'}),
        walks=supabase_get('walks', {'select': '*,dogs(dog_name)', 'order': 'walk_date.desc'}),
        editing='new', form={})

@app.route('/payments/<id>/delete', methods=['POST'])
def delete_payment(id):
    supabase_delete('payments', id)
    flash('Payment deleted', 'success')
    return redirect(url_for('list_payments'))

@app.route('/api/trigger-booking/<walk_id>', methods=['POST'])
def trigger_booking(walk_id):
    try:
        w = supabase_get('walks', {
            'select': '*,dogs(dog_name,customer_id(first_name,last_name,email,phone)),walkers(first_name,last_name,email)',
            'id': f'eq.{walk_id}'
        })
        if not w:
            return jsonify({'status': 'error', 'message': 'Walk not found'}), 404
        w = w[0]
        payload = {
            'walk_id': str(w['id']),
            'walk_date': str(w.get('walk_date','')),
            'status': w.get('status',''),
            'dog_name': w.get('dogs',{}).get('dog_name',''),
            'customer_name': fmt_name(w.get('dogs',{}).get('customer_id',{})),
            'customer_email': w.get('dogs',{}).get('customer_id',{}).get('email',''),
            'customer_phone': w.get('dogs',{}).get('customer_id',{}).get('phone',''),
            'walker_name': fmt_name(w.get('walkers',{})),
            'walker_email': w.get('walkers',{}).get('email','')
        }
        r = requests.post(Config.N8N_BOOKING_URL, json=payload, timeout=15)
        return jsonify({'status': 'ok', 'n8n_status': r.status_code, 'response': r.text[:500]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/trigger-completion/<walk_id>', methods=['POST'])
def trigger_completion(walk_id):
    try:
        w = supabase_get('walks', {
            'select': '*,dogs(dog_name,customer_id(first_name,last_name,email)),walkers(first_name,last_name,email)',
            'id': f'eq.{walk_id}'
        })
        if not w:
            return jsonify({'status': 'error', 'message': 'Walk not found'}), 404
        w = w[0]
        payload = {
            'walk_id': str(w['id']),
            'walk_date': str(w.get('walk_date','')),
            'status': w.get('status',''),
            'dog_name': w.get('dogs',{}).get('dog_name',''),
            'customer_name': fmt_name(w.get('dogs',{}).get('customer_id',{})),
            'customer_email': w.get('dogs',{}).get('customer_id',{}).get('email',''),
            'walker_name': fmt_name(w.get('walkers',{})),
            'walker_email': w.get('walkers',{}).get('email','')
        }
        r = requests.post(Config.N8N_COMPLETION_URL, json=payload, timeout=15)
        return jsonify({'status': 'ok', 'n8n_status': r.status_code, 'response': r.text[:500]})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=os.getenv('FLASK_ENV') == 'development', host='0.0.0.0', port=port)

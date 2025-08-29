HTML = """
<!doctype html><html><head>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>ALGOM Admin</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:0;background:#0e1117;color:#e6edf3}
.header{padding:16px;background:#111827;position:sticky;top:0}
.container{padding:16px}
.card{background:#111827;border:1px solid #1f2937;border-radius:16px;padding:16px;margin-bottom:16px}
input,button{padding:12px;border-radius:12px;border:1px solid #374151;background:#0b1220;color:#e6edf3;width:100%;margin-top:8px}
button{cursor:pointer}
table{width:100%;border-collapse:collapse}
th,td{border-bottom:1px solid #1f2937;padding:8px;text-align:left}
.badge{display:inline-block;padding:4px 8px;border-radius:8px;background:#1f2937}
</style></head><body>
<div class="header"><b>ALGOM Admin</b></div>
<div class="container">
{% if not ok %}
  <div class="card"><h3>Enter Admin PIN</h3>
    <form method="POST">
      <input type="password" name="pin" inputmode="numeric" pattern="\\d{4}" placeholder="4-digit PIN" required>
      <button type="submit">Unlock</button>
    </form>
  </div>
{% else %}
  <div class="card">
    <h3>Overview</h3>
    <div>Users: <span class="badge">{{ s.users }}</span></div>
    <div>Daily Active (24h): <span class="badge">{{ s.daily_active }}</span></div>
    <div>Coins Awarded: <span class="badge">{{ s.coins }}</span></div>
    <a href="/export?pin={{ pin }}"><button>Export CSV</button></a>
  </div>
  <div class="card">
    <h3>Users</h3>
    <form method="GET">
      <input type="hidden" name="pin" value="{{ pin }}">
      <input name="q" placeholder="Search email/wallet/username">
    </form>
    <div style="overflow:auto">
      <table>
        <tr><th>User ID</th><th>Name</th><th>Username</th><th>Email</th><th>Wallet</th><th>Balance</th><th>Referrer</th><th>Total Taps</th></tr>
        {% for u in users %}
          <tr>
            <td>{{ u.get('user_id') }}</td>
            <td>{{ (u.get('first_name') or '') + ' ' + (u.get('last_name') or '') }}</td>
            <td>@{{ u.get('username') or '' }}</td>
            <td>{{ u.get('email') or '' }}</td>
            <td>{{ u.get('wallet') or '' }}</td>
            <td>{{ u.get('balance') or 0 }}</td>
            <td>{{ u.get('referrer') or '' }}</td>
            <td>{{ u.get('total_taps') or 0 }}</td>
          </tr>
        {% endfor %}
      </table>
    </div>
  </div>
{% endif %}
</div></body></html>
"""

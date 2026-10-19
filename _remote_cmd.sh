echo "=== SERVICES ==="
systemctl list-units --type=service --no-pager | grep -iE 'fire|safety|fs'
echo "=== PROCS ==="
ps aux | grep -iE 'gunicorn|flask' | grep -v grep
echo "=== FIND manage_routes ==="
find / -maxdepth 5 -name 'manage_routes.py' 2>/dev/null
echo "=== FIND fire backend ==="
find / -maxdepth 4 -type d -iname '*fire*' 2>/dev/null
echo "=== FIND fs-admin ==="
ls -la /opt/ 2>/dev/null
echo "=== DB ==="
mysql -uroot -e 'SHOW DATABASES;' 2>/dev/null

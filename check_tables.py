import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()
cursor.execute("SHOW TABLES LIKE 'analyst_%'")
print('Analyst tables:')
for table in cursor.fetchall():
    print(table[0])
conn.close()
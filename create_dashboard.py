import pymysql
conn = pymysql.connect(host='192.168.18.59', user='m360user', password='m360pass', database='projects')
cursor = conn.cursor()

# Create analyst_dashboard table
sql_dashboard = '''
CREATE TABLE `analyst_dashboard` (
  `id` uuid NOT NULL PRIMARY KEY,
  `name` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `is_public` bool NOT NULL,
  `layout` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `created_by_id` bigint NOT NULL
)
'''
try:
    cursor.execute(sql_dashboard)
    print('Table analyst_dashboard created successfully')
except Exception as e:
    print('Error creating analyst_dashboard table:', e)

# Create analyst_dashboardwidget table
sql_dashboardwidget = '''
CREATE TABLE `analyst_dashboardwidget` (
  `id` uuid NOT NULL PRIMARY KEY,
  `widget_type` varchar(20) NOT NULL,
  `title` varchar(200) NOT NULL,
  `source` json NOT NULL,
  `config` json NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `dashboard_id` uuid NOT NULL
)
'''
try:
    cursor.execute(sql_dashboardwidget)
    print('Table analyst_dashboardwidget created successfully')
except Exception as e:
    print('Error creating analyst_dashboardwidget table:', e)

# Add foreign key constraints for analyst_dashboard
try:
    fk1 = '''ALTER TABLE `analyst_dashboard` 
    ADD CONSTRAINT `analyst_dashboard_created_by_id_d0291b0e_fk_accounts_user_id` 
    FOREIGN KEY (`created_by_id`) REFERENCES `accounts_user` (`id`)'''
    cursor.execute(fk1)
    print('Created_by foreign key added to analyst_dashboard')
except Exception as e:
    print('Error adding created_by foreign key to analyst_dashboard:', e)

# Add foreign key constraints for analyst_dashboardwidget
try:
    fk2 = '''ALTER TABLE `analyst_dashboardwidget` 
    ADD CONSTRAINT `analyst_dashboardwid_dashboard_id_54fb2875_fk_analyst_d` 
    FOREIGN KEY (`dashboard_id`) REFERENCES `analyst_dashboard` (`id`)'''
    cursor.execute(fk2)
    print('Dashboard foreign key added to analyst_dashboardwidget')
except Exception as e:
    print('Error adding dashboard foreign key to analyst_dashboardwidget:', e)

conn.close()
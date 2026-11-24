def migrate(cr, version):
    cr.execute("DROP INDEX IF EXISTS stage_rules_unique_active_scope")
    cr.execute("""
        ALTER TABLE stage_rules
            ALTER COLUMN stage_id DROP NOT NULL,
            ALTER COLUMN e_target_field DROP NOT NULL
    """)

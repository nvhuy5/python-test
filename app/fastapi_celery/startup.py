from connections.postgres_conn import (
    MappingRules,
    get_session
)

def init_mapping_rules():
    # Get a new session instance to interact with the database
    session = get_session()
    
    try:
        # Check if the mapping rule for 'Customer-001' exists
        mapping_rule_customer_001 = session.query(MappingRules).filter(MappingRules.customer_name == 'Customer-001').first()
        if not mapping_rule_customer_001:
            # Insert mapping rule for 'Customer-001' if not exists
            new_mapping_rule = MappingRules(
                customer_name="Customer-001",
                rules=['step 1', 'step 2', 'step 3', 'step 4', 'step 5']
            )
            session.add(new_mapping_rule)
        
        # Check if the mapping rule for 'Customer-002' exists
        mapping_rule_customer_002 = session.query(MappingRules).filter(MappingRules.customer_name == 'Customer-002').first()
        if not mapping_rule_customer_002:
            # Insert mapping rule for 'Customer-002' if not exists
            new_mapping_rule = MappingRules(
                customer_name="Customer-002",
                rules=['step 2', 'step 1', 'step 5']
            )
            session.add(new_mapping_rule)
        
        # Commit the transaction to save the changes to the database
        session.commit()

    except Exception as e:
        # Handle any errors during the operation
        print(f"Error initializing mapping rules: {e}")
    finally:
        # Close the session after the operation
        session.close()

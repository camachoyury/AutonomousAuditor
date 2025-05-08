from agent import FinancialDocument

def test_markdown_parser():
    print("Probando parser de Markdown...")
    with open('test_pl.md', 'r') as f:
        content = f.read()
    
    doc = FinancialDocument(content, 'pl')
    result = doc.parse()
    
    print("\nPeríodo:", result['period'])
    
    print("\nIngresos:")
    for item in result['revenue']:
        print(f"- {item.name}: ${item.amount:,.2f}")
    
    print("\nGastos:")
    for item in result['expenses']:
        print(f"- {item.name}: ${item.amount:,.2f}")
    
    print("\nTotales:")
    for name, amount in result['totals'].items():
        print(f"- {name}: ${amount:,.2f}")

def test_csv_parser():
    print("\nProbando parser de CSV...")
    with open('test_pl.csv', 'r') as f:
        content = f.read()
    
    doc = FinancialDocument(content, 'pl')
    result = doc.parse()
    
    print("\nIngresos:")
    for item in result['revenue']:
        print(f"- {item.name}: ${item.amount:,.2f}")
    
    print("\nGastos:")
    for item in result['expenses']:
        print(f"- {item.name}: ${item.amount:,.2f}")
    
    print("\nTotales:")
    for name, amount in result['totals'].items():
        print(f"- {name}: ${amount:,.2f}")

if __name__ == "__main__":
    test_markdown_parser()
    test_csv_parser() 
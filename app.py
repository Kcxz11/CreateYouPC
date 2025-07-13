from flask import Flask, render_template, request, jsonify
import json
import random
import os

app = Flask(__name__)

def load_builds():
    """Carga la base de datos de componentes desde builds.json"""
    try:
        with open('builds.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"components": {}}

def generate_build(budget, use_type):
    """
    Genera una build personalizada basada en el presupuesto y tipo de uso
    """
    builds_data = load_builds()
    components = builds_data.get("components", {})
    
    # Definir porcentajes de presupuesto por componente según el tipo de uso
    budget_allocation = {
        "gaming": {
            "cpu": 0.25,
            "gpu": 0.40,
            "ram": 0.12,
            "storage": 0.10,
            "motherboard": 0.08,
            "psu": 0.05
        },
        "design": {
            "cpu": 0.35,
            "gpu": 0.30,
            "ram": 0.20,
            "storage": 0.08,
            "motherboard": 0.05,
            "psu": 0.02
        },
        "office": {
            "cpu": 0.40,
            "gpu": 0.15,
            "ram": 0.20,
            "storage": 0.15,
            "motherboard": 0.08,
            "psu": 0.02
        },
        "streaming": {
            "cpu": 0.30,
            "gpu": 0.35,
            "ram": 0.15,
            "storage": 0.12,
            "motherboard": 0.06,
            "psu": 0.02
        }
    }
    
    allocation = budget_allocation.get(use_type, budget_allocation["office"])
    selected_build = {}
    
    # Seleccionar componentes basados en el presupuesto asignado
    for component_type, percentage in allocation.items():
        component_budget = budget * percentage
        available_components = components.get(component_type, [])
        
        # Filtrar componentes que estén dentro del presupuesto
        suitable_components = [
            comp for comp in available_components 
            if comp["price"] <= component_budget * 1.2  # 20% de flexibilidad
        ]
        
        if suitable_components:
            # Seleccionar el componente más cercano al presupuesto ideal
            best_component = min(suitable_components, 
                               key=lambda x: abs(x["price"] - component_budget))
            selected_build[component_type] = best_component
        elif available_components:
            # Si no hay componentes en el rango, seleccionar el más barato
            selected_build[component_type] = min(available_components, 
                                               key=lambda x: x["price"])
    
    # Agregar gabinete (case) como componente adicional
    if "case" in components:
        case_budget = budget * 0.05
        suitable_cases = [
            case for case in components["case"] 
            if case["price"] <= case_budget * 1.5
        ]
        if suitable_cases:
            selected_build["case"] = random.choice(suitable_cases)
        elif components["case"]:
            selected_build["case"] = components["case"][0]
    
    # Calcular precio total
    total_price = sum(comp["price"] for comp in selected_build.values())
    
    return {
        "build": selected_build,
        "total_price": total_price,
        "budget": budget,
        "use_type": use_type
    }

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/build', methods=['POST'])
def create_build():
    """
    Endpoint para generar una build personalizada
    Recibe: budget (int), use_type (string)
    Retorna: JSON con la build sugerida
    """
    try:
        data = request.get_json()
        budget = int(data.get('budget', 1000))
        use_type = data.get('use_type', 'office').lower()
        
        # Validar presupuesto mínimo
        if budget < 300:
            return jsonify({
                "error": "El presupuesto mínimo es de $300 USD"
            }), 400
        
        # Generar build
        build_result = generate_build(budget, use_type)
        
        return jsonify({
            "success": True,
            "build": build_result["build"],
            "total_price": build_result["total_price"],
            "budget": build_result["budget"],
            "use_type": build_result["use_type"],
            "message": f"¡Build generada exitosamente para {use_type}!"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error al generar la build: {str(e)}"
        }), 500

@app.route('/health')
def health_check():
    """Endpoint de salud para verificar que la aplicación funciona"""
    return jsonify({"status": "healthy", "message": "CreateYouPC API is running!"})

if __name__ == '__main__':
    # Configuración para desarrollo local
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
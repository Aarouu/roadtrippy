import os
import json
import sqlite3
import math
import osmnx as ox
import networkx as nx
from flask import Flask, jsonify, render_template, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db  

 
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_key")

DB_NAME = "roads.db"


# Initialize DB if not exists
if not os.path.exists(DB_NAME):
    init_db()

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# Graph Cache
graph_cache = {}


# Haversine Distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (
        math.sin(dLat/2)**2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(dLon/2)**2
    )
    return 2 * R * math.asin(math.sqrt(a))


#Graph_Retrieval
def get_graph_for_area(start_lat, start_lon, end_lat, end_lon):
    """Get or download a road network graph for the area between two points."""
    distance_km = haversine(start_lat, start_lon, end_lat, end_lon)
    radius = max(int(distance_km * 1000 * 1.5), 5000)  # minimum 5 km
    radius = min(radius, 50000)

    center_lat = (start_lat + end_lat) / 2
    center_lon = (start_lon + end_lon) / 2
    cache_key = (round(center_lat,2), round(center_lon,2), round(radius,-3))

    if cache_key in graph_cache:
        return graph_cache[cache_key]

    #Retry
    for attempt in range(3):
        try:
            G = ox.graph_from_point((center_lat, center_lon), dist=radius, network_type="drive")
            G = ox.add_edge_speeds(G)
            G = ox.add_edge_travel_times(G)
            if len(G) > 0:
                graph_cache[cache_key] = G
                return G
        except Exception as e:
            print(f"OSMnx attempt {attempt+1} failed:", e)
        radius *= 2  # expand search area
    return None


# A* Route Finder
def haversine_distance_nodes(G, n1, n2):
    y1, x1 = G.nodes[n1]["y"], G.nodes[n1]["x"]
    y2, x2 = G.nodes[n2]["y"], G.nodes[n2]["x"]
    return haversine(y1, x1, y2, x2)

def find_route_astar(G, start_lat, start_lon, end_lat, end_lon):
    if not G:
        return None, 0

    G = ox.project_graph(G)
    start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
    end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

    try:
        # A* shortest path using travel_time and Haversine heuristic
        route = nx.astar_path(
            G, start_node, end_node,
            heuristic=lambda u, v: haversine_distance_nodes(G, u, v),
            weight="travel_time"
        )

        # Route coordinates
        route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]

        # Sum travel times robustly
        total_time = 0
        for u, v in zip(route[:-1], route[1:]):
            edge_data = list(G.get_edge_data(u, v).values())[0]
            travel_time = edge_data.get("travel_time")
            if travel_time is None:
                length = edge_data.get("length", 0)
                speed_kph = edge_data.get("speed_kph", 30)
                travel_time = length / 1000 / speed_kph * 3600
            total_time += travel_time

        return route_coords, total_time

    except nx.NetworkXNoPath:
        return None, 0


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        if not username or not password:
            flash("Username and password cannot be empty.", "error")
            return redirect("/register")
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
            flash("Registration successful! You can now log in.", "success")
            return redirect("/login")
        except sqlite3.IntegrityError:
            flash("Username is already taken.", "error")
            return redirect("/register")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        if not user:
            flash("Username does not exist.", "error")
            return redirect("/login")
        if not check_password_hash(user["password"], password):
            flash("Incorrect password.", "error")
            return redirect("/login")
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        flash("Welcome back!", "success")
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")


@app.route("/route", methods=["POST"])
def route_api():
    data = request.get_json()
    start_lat, start_lon = data["start"]
    end_lat, end_lon = data["end"]

    G = get_graph_for_area(start_lat, start_lon, end_lat, end_lon)
    if not G:
        return jsonify({"error": "No road network found for this area"}), 400

    try:
        start_node = ox.distance.nearest_nodes(G, X=start_lon, Y=start_lat)
        end_node = ox.distance.nearest_nodes(G, X=end_lon, Y=end_lat)

        route = nx.astar_path(G, start_node, end_node, weight="travel_time")
        route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in route]

        # Sum travel times
        total_time = sum(list(G[u][v][0].get("travel_time", 0) for u,v in zip(route[:-1], route[1:])))

        return jsonify({
            "coords": route_coords,
            "time": round(total_time / 60, 1)
        })
    except (nx.NetworkXNoPath, ValueError):
        return jsonify({"error": "No route found"}), 400


# Favorites
@app.route("/save_favorite", methods=["POST"])
def save_favorite():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 403
    data = request.get_json()
    name = data.get("name", "Unnamed road")
    geometry = json.dumps(data["coords"])
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO favorite_roads (name, geometry, user_id) VALUES (?, ?, ?)",
        (name, geometry, session["user_id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "saved"})

@app.route("/favorites")
def favorites():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT fr.id, fr.name, fr.geometry,
               AVG(r.rating) as avg_rating, COUNT(r.rating) as rating_count
        FROM favorite_roads fr
        LEFT JOIN ratings r ON fr.id = r.road_id
        GROUP BY fr.id
    """)
    rows = c.fetchall()
    conn.close()
    roads = []
    for row in rows:
        roads.append({
            "id": row["id"],
            "name": row["name"],
            "coords": json.loads(row["geometry"]),
            "avg_rating": round(row["avg_rating"],1) if row["avg_rating"] else None,
            "rating_count": row["rating_count"]
        })
    return jsonify(roads)


# Rating
@app.route("/rate", methods=["POST"])
def rate():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 403
    data = request.get_json()
    road_id = data["road_id"]
    rating = int(data["rating"])
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO ratings (user_id, road_id, rating)
        VALUES (?, ?, ?)
    """, (session["user_id"], road_id, rating))
    conn.commit()
    conn.close()
    return jsonify({"status": "rated"})


# Run App
if __name__ == "__main__":
    app.run(debug=True, port=8080)

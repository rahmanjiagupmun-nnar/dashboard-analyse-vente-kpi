import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

# Chargement des données
try:
    df = pd.read_excel("data_kpi.xlsx")

    # Afficher les colonnes pour debug
    print("Colonnes détectées dans le fichier Excel :")
    print(df.columns.tolist())

    # Normalisation et nettoyage des colonnes
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("(", "")
        .str.replace(")", "")
        .str.replace("€", "")
        .str.replace("é", "e")
        .str.replace("è", "e")
        .str.replace("ê", "e")
        .str.replace("à", "a")
    )

    # Renommage des colonnes
    df.rename(columns={
        "id_client": "ID_Client",
        "client": "ID_Client",
        "client_id": "ID_Client",

        "montant": "Montant",
        "montant_transaction": "Montant",
        "montant_de_la_transaction": "Montant",
        "montant_eur": "Montant",
        "valeur": "Montant",
        "amount": "Montant",

        "categorie": "Categorie",
        "categorie_produit": "Categorie",

        "mode_paiement": "Mode_Paiement",
        "paiement": "Mode_Paiement"
    }, inplace=True)

    
    if "Montant" not in df.columns:
        colonnes_numeriques = df.select_dtypes(include="number").columns.tolist()
        if len(colonnes_numeriques) == 1:
            df.rename(columns={colonnes_numeriques[0]: "Montant"}, inplace=True)
        else:
            raise ValueError(f"Impossible d'identifier la colonne Montant. Colonnes numériques trouvées : {colonnes_numeriques}")

    print("Colonnes finales utilisées :", df.columns.tolist())
        
except FileNotFoundError:
    print("Fichier data_kpi.xlsx non trouvé")



# Conversion la colonne Montant en numérique et Suppression des lignes où Montant est NaN
df['Montant'] = pd.to_numeric(df['Montant'], errors='coerce')

df = df.dropna(subset=['Montant'])


# ===== CALCULS DES KPI =====

# 1- Valeur moyenne des transactions
moyenne_transaction = df['Montant'].mean()
total_ventes = df['Montant'].sum()
nb_transactions = len(df)

# 2-  Répartition par catégorie
categorie_ventes = df.groupby('Categorie')['Montant'].sum()
categorie_pourcentage = (categorie_ventes / total_ventes * 100).round(1)

# 3- Taux de récurrence des clients
client_transactions = df.groupby('ID_Client').size()
clients_recurrents = (client_transactions > 1).sum()
nb_clients = len(client_transactions)
taux_recurrence = (clients_recurrents / nb_clients * 100).round(1)

# 4- Modes de paiement
paiement_count = df['Mode_Paiement'].value_counts()
paiement_pourcentage = (paiement_count / nb_transactions * 100).round(1)

# 5-  CLV moyenne
clv_par_client = df.groupby('ID_Client')['Montant'].sum()
clv_moyenne = clv_par_client.mean()

# 6-  Meilleure catégorie
meilleure_categorie = categorie_ventes.idxmax()
meilleur_ca = categorie_ventes.max()

# ===== CRÉATION DES GRAPHIQUES =====

# Graphique 1: Répartition par catégorie (Pie Chart)
fig_categorie = go.Figure(data=[go.Pie(
    labels=categorie_pourcentage.index,
    values=categorie_pourcentage.values,
    hole=0.3,
    marker_colors=px.colors.qualitative.Set2
)])
fig_categorie.update_layout(
    title="Répartition des Ventes par Catégorie (%)",
    height=400
)

# Graphique 2: Modes de paiement (Pie Chart)
fig_paiement = go.Figure(data=[go.Pie(
    labels=paiement_pourcentage.index,
    values=paiement_pourcentage.values,
    hole=0.3,
    marker_colors=px.colors.qualitative.Pastel
)])
fig_paiement.update_layout(
    title="Répartition des Modes de Paiement (%)",
    height=400
)

# Graphique 3: Chiffre d'affaires par catégorie (Bar Chart)
fig_ca = go.Figure(data=[go.Bar(
    x=categorie_ventes.index,
    y=categorie_ventes.values,
    marker_color=px.colors.qualitative.Bold,
    text=categorie_ventes.values.round(0),
    textposition='auto'
)])
fig_ca.update_layout(
    title="Chiffre d'Affaires par Catégorie (€)",
    xaxis_title="Catégorie",
    yaxis_title="Montant (€)",
    height=400
)

# ===== CRÉATION DU DASHBOARD DASH =====

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    # En-tête
    dbc.Row([
        dbc.Col([
            html.H1("📊 Dashboard KPI - Analyse des Ventes", className="text-center mb-2 mt-4"),
            html.P(f"Analyse de {nb_transactions} transactions", className="text-center text-muted mb-4")
        ])
    ]),
    
    # KPI Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("💰 Valeur Moyenne", className="card-subtitle mb-2 text-muted"),
                    html.H2(f"{moyenne_transaction:.2f} €", className="card-title text-primary"),
                    html.P("Par transaction", className="card-text small")
                ])
            ], className="shadow-sm mb-4")
        ], width=12, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("📈 Total des Ventes", className="card-subtitle mb-2 text-muted"),
                    html.H2(f"{total_ventes:,.0f} €", className="card-title text-success"),
                    html.P(f"{nb_transactions} transactions", className="card-text small")
                ])
            ], className="shadow-sm mb-4")
        ], width=12, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("👥 Taux de Récurrence", className="card-subtitle mb-2 text-muted"),
                    html.H2(f"{taux_recurrence:.1f} %", className="card-title text-info"),
                    html.P(f"{clients_recurrents} / {nb_clients} clients", className="card-text small")
                ])
            ], className="shadow-sm mb-4")
        ], width=12, md=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("💎 CLV Moyenne", className="card-subtitle mb-2 text-muted"),
                    html.H2(f"{clv_moyenne:.2f} €", className="card-title text-warning"),
                    html.P("Customer Lifetime Value", className="card-text small")
                ])
            ], className="shadow-sm mb-4")
        ], width=12, md=3),
    ], className="mb-4"),
    
    # Graphiques en ligne
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(figure=fig_categorie)
                ])
            ], className="shadow-sm")
        ], width=12, md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(figure=fig_paiement)
                ])
            ], className="shadow-sm")
        ], width=12, md=6),
    ], className="mb-4"),
    
    # Graphique CA + Insights
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(figure=fig_ca)
                ])
            ], className="shadow-sm")
        ], width=12, md=8),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("🏆 Insights Clés", className="mb-3"),
                    html.Hr(),
                    html.P([
                        html.Strong("Meilleure catégorie: "),
                        html.Span(f"{meilleure_categorie}", className="text-primary")
                    ]),
                    html.P([
                        html.Strong("CA généré: "),
                        html.Span(f"{meilleur_ca:,.0f} €", className="text-success")
                    ]),
                    html.Hr(),
                    html.P([
                        html.Strong("Mode de paiement préféré: "),
                        html.Span(f"{paiement_count.index[0]}", className="text-info")
                    ]),
                    html.P([
                        html.Strong("Usage: "),
                        html.Span(f"{paiement_pourcentage.iloc[0]}%", className="text-muted")
                    ]),
                    html.Hr(),
                    html.P([
                        html.Strong("Panier moyen: "),
                        html.Span(f"{moyenne_transaction:.2f} €", className="text-warning")
                    ]),
                    html.P([
                        html.Strong("Clients fidèles: "),
                        html.Span(f"{taux_recurrence:.1f}%", className="text-danger")
                    ])
                ])
            ], className="shadow-sm h-100", style={"backgroundColor": "#f8f9fa"})
        ], width=12, md=4)
    ])
    
], fluid=True, style={"backgroundColor": "#f0f2f5"})

if __name__ == '__main__':
    app.run(debug=True, port=8050)
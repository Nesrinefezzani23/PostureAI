import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const PostureApp());
}

class PostureApp extends StatelessWidget {
  const PostureApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        scaffoldBackgroundColor: Colors.grey[50],
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      home: const LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _isLoading = false;
  
  final String _apiUrl = "http://192.168.100.26:8000/login-api/";

  Future<void> _login() async {
    setState(() => _isLoading = true);
    try {
      final response = await http.post(
        Uri.parse(_apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "username": _usernameController.text,
          "password": _passwordController.text,
        }),
      );

      if (!mounted) return;

      if (response.statusCode == 200) {
        var data = jsonDecode(response.body);
        String accessToken = data['access'];
        
        // Sauvegarde locale
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('token', accessToken);

        // Redirection vers le Dashboard
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const DashboardScreen()),
        );
      } else {
        _showResultDialog("Erreur", "Identifiants invalides.", Icons.error, Colors.red);
      }
    } catch (e) {
      if (!mounted) return;
      _showResultDialog("Erreur", "Impossible de joindre le serveur.", Icons.signal_wifi_off, Colors.orange);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showResultDialog(String title, String message, IconData icon, Color color) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(children: [Icon(icon, color: color), const SizedBox(width: 10), Text(title)]),
        content: Text(message),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text("OK"))],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.accessibility_new, size: 80, color: Colors.indigo),
              const SizedBox(height: 30),
              const Text("Connexion PostureAI", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.indigo)),
              const SizedBox(height: 30),
              TextField(controller: _usernameController, decoration: const InputDecoration(labelText: "Nom d'utilisateur", prefixIcon: Icon(Icons.person))),
              const SizedBox(height: 16),
              TextField(controller: _passwordController, decoration: const InputDecoration(labelText: "Mot de passe", prefixIcon: Icon(Icons.lock)), obscureText: true),
              const SizedBox(height: 30),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.indigo, foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                  onPressed: _isLoading ? null : _login,
                  child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text("SE CONNECTER", style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<List<dynamic>> _alertsFuture;

  @override
  void initState() {
    super.initState();
    _alertsFuture = fetchAlerts();
  }

  Future<List<dynamic>> fetchAlerts() async {
    final prefs = await SharedPreferences.getInstance();
    final String? token = prefs.getString('token');
    final String url = "http://192.168.100.26:8000/api/alertes/";

    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Erreur lors du chargement des alertes');
      }
    } catch (e) {
      print("Erreur réseau : $e");
      return [];
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("PostureAI - Dashboard"), backgroundColor: Colors.indigo),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildStatusHeader(),
          const SizedBox(height: 20),
          _buildAlertSection(),
          const SizedBox(height: 20),
          _buildRecommendationSection(),
        ],
      ),
    );
  }

  Widget _buildStatusHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(color: Colors.green[100], borderRadius: BorderRadius.circular(15)),
      child: const Row(
        children: [
          Icon(Icons.check_circle, color: Colors.green, size: 40),
          SizedBox(width: 15),
          Text("Posture Correcte", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildAlertSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text("Dernières Alertes", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),
        FutureBuilder<List<dynamic>>(
          future: _alertsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            } else if (snapshot.hasError || !snapshot.hasData || snapshot.data!.isEmpty) {
              return const Card(child: Padding(padding: EdgeInsets.all(16.0), child: Text("Aucune alerte pour le moment.")));
            }

            return ListView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: snapshot.data!.length,
              itemBuilder: (context, index) {
                var alerte = snapshot.data![index];
                return Card(
                  child: ListTile(
                    leading: Icon(
                      alerte['type'] == 'warning' ? Icons.warning : Icons.info,
                      color: alerte['type'] == 'warning' ? Colors.orange : Colors.blue,
                    ),
                    title: Text(alerte['titre'] ?? 'Alerte'),
                    subtitle: Text("${alerte['message'] ?? ''} (${alerte['temps'] ?? ''})"),
                  ),
                );
              },
            );
          },
        ),
      ],
    );
  }

  Widget _buildRecommendationSection() {
    return Card(
      color: Colors.indigo[50],
      child: const Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text("💡 Recommandation IA", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.indigo)),
            SizedBox(height: 8),
            Text("Pensez à faire une pause de 2 minutes et à étirer vos épaules."),
          ],
        ),
      ),
    );
  }
}

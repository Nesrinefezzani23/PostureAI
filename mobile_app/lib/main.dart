import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import 'package:vibration/vibration.dart';

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
        
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('token', accessToken);

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
  late WebSocketChannel channel;
  late Stream _broadcastStream;
  bool _wasPostureBad = false;

  @override
  void initState() {
    super.initState();
    connectToWebSocket();
  }

  void connectToWebSocket() {
    channel = WebSocketChannel.connect(
      Uri.parse('ws://192.168.100.26:8000/ws/posture/'),
    );
    
    _broadcastStream = channel.stream.asBroadcastStream();

    _broadcastStream.listen(
      (data) {
        var decoded = jsonDecode(data.toString());
        _checkVibration(decoded['score_posture'] ?? 100);
      },
      onDone: () {
        print("WebSocket déconnecté. Reconnexion dans 2 secondes...");
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) connectToWebSocket();
        });
      },
      onError: (error) {
        print("Erreur WebSocket: $error");
      },
    );
  }

  void _checkVibration(int score) {
    print("Debug: Checking vibration for score: $score. _wasPostureBad: $_wasPostureBad");
    bool isWarning = score < 50;
    if (isWarning && !_wasPostureBad) {
      print("Debug: Triggering vibration!");
      _wasPostureBad = true;
      Vibration.vibrate(
        pattern: [0, 500, 200, 500],
        intensities: [0, 255, 0, 255],
      );
    } else if (!isWarning) {
      _wasPostureBad = false;
    }
  }

  @override
  void dispose() {
    channel.sink.close(status.goingAway);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("PostureAI - Dashboard"), backgroundColor: Colors.indigo),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          _buildLiveStatus(),
          const SizedBox(height: 20),
          _buildRecommendationSection(),
        ],
      ),
    );
  }

  Widget _buildLiveStatus() {
    return StreamBuilder(
      stream: _broadcastStream,
      builder: (context, snapshot) {
        if (snapshot.hasError) return Text('Erreur: ${snapshot.error}');
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());

        print("Debug: Raw WS data: ${snapshot.data}");
        var data = jsonDecode(snapshot.data.toString());
        int score = data['score_posture'] ?? 100;
        bool isWarning = score < 50;
        Color statusColor = isWarning ? Colors.red : Colors.green;

        return Card(
          color: isWarning ? Colors.red[100] : Colors.green[100],
          child: ListTile(
            leading: Icon(isWarning ? Icons.warning : Icons.check_circle, color: statusColor, size: 40),
            title: Text("Score Posture: $score", style: TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text("Statut: ${data['statut'] ?? 'Inconnu'}"),
            trailing: Text("${DateTime.now().hour}:${DateTime.now().minute}"),
          ),
        );
      },
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

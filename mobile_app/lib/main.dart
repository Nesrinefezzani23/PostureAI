import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import 'package:vibration/vibration.dart';
import 'package:audioplayers/audioplayers.dart';

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
  bool _isPasswordVisible = false;
  
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
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            children: [
              const SizedBox(height: 120),
              Image.asset('assets/img/Logo.png', height: 250),
              TextField(
                controller: _usernameController,
                decoration: const InputDecoration(labelText: "Nom d'utilisateur", prefixIcon: Icon(Icons.person), border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _passwordController,
                obscureText: !_isPasswordVisible,
                decoration: InputDecoration(
                  labelText: "Mot de passe",
                  prefixIcon: const Icon(Icons.lock),
                  suffixIcon: IconButton(
                    icon: Icon(_isPasswordVisible ? Icons.visibility : Icons.visibility_off),
                    onPressed: () => setState(() => _isPasswordVisible = !_isPasswordVisible),
                  ),
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 32),
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
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _wasPostureBad = false;
  int _secondsGreen = 0;
  int _secondsRed = 0;

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
        int score = decoded['score_posture'] ?? 100;
        
        setState(() {
          if (score >= 50) _secondsGreen++; else _secondsRed++;
        });
        
        _triggerAlert(score);
      },
      onDone: () {
        print("WebSocket déconnecté. Reconnexion...");
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) connectToWebSocket();
        });
      },
      onError: (error) {
        print("Erreur WebSocket: $error");
      },
    );
  }

  Future<void> _triggerAlert(int score) async {
    bool isWarning = score < 50;
    if (isWarning && !_wasPostureBad) {
      _wasPostureBad = true;

      // 1. Déclencher la vibration
      if (await Vibration.hasVibrator() ?? false) {
        Vibration.vibrate(pattern: [0, 500, 200, 500]);
      }

      // 2. Jouer le son "Bip"
      await _audioPlayer.play(AssetSource('audio/bip.mp3'));
    } else if (!isWarning) {
      _wasPostureBad = false;
    }
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    channel.sink.close(status.goingAway);
    super.dispose();
  }

  Widget _buildCard({required Widget child}) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(padding: const EdgeInsets.all(16.0), child: child),
    );
  }

  Widget _buildStatsSection() {
    final double total = (_secondsGreen + _secondsRed).toDouble();
    if (total == 0) return const SizedBox.shrink();

    final int greenPercent = (_secondsGreen / total * 100).toInt();
    final int redPercent = (_secondsRed / total * 100).toInt();

    return _buildCard(
      child: Column(
        children: [
          const Text("Répartition du temps de posture", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 20),
          SizedBox(
            height: 200,
            child: PieChart(
              PieChartData(
                sectionsSpace: 2,
                centerSpaceRadius: 40,
                sections: [
                  PieChartSectionData(value: _secondsGreen.toDouble(), color: Colors.teal, title: '$greenPercent%', radius: 60, titleStyle: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                  PieChartSectionData(value: _secondsRed.toDouble(), color: Colors.redAccent, title: '$redPercent%', radius: 60, titleStyle: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildLegendItem(Colors.teal, "Correcte"),
              _buildLegendItem(Colors.redAccent, "Incorrecte"),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(Color color, String text) {
    return Row(
      children: [
        Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 8),
        Text(text, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 150.0,
            floating: false,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              title: const Text("PostureAI", style: TextStyle(fontWeight: FontWeight.bold)),
              background: Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    colors: [Colors.indigo, Colors.blueAccent],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.all(16.0),
            sliver: SliverList(
              delegate: SliverChildListDelegate([
                _buildLiveStatus(),
                const SizedBox(height: 16),
                _buildStatsSection(),
                const SizedBox(height: 16),
                _buildRecommendationSection(),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveStatus() {
    return StreamBuilder(
      stream: _broadcastStream,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Card(color: Colors.red[100], child: ListTile(title: Text("Erreur: ${snapshot.error}")));
        }
        
        switch (snapshot.connectionState) {
          case ConnectionState.waiting:
          case ConnectionState.active:
            if (!snapshot.hasData) {
              return const Card(
                child: Padding(
                  padding: EdgeInsets.all(20),
                  child: Row(
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(width: 20),
                      Text("Connexion au capteur..."),
                    ],
                  ),
                ),
              );
            }
            break;
          case ConnectionState.done:
            return const Card(child: ListTile(title: Text("Connexion fermée par le serveur.")));
          default:
            return const Card(child: ListTile(title: Text("En attente...")));
        }

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

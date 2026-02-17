# Chapter 9: Flutter Mobile App

[← Previous: FastAPI Backend](08-fastapi-backend.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Testing & Deployment →](10-testing-deployment.md)

---

## 9.1 Flutter App Overview

The Flutter app provides a beautiful mobile interface for the backend API. It has **6 screens** organized with a bottom navigation bar.

### App Architecture

```
app/
├── lib/
│   ├── main.dart            ← App entry point, theming, navigation
│   ├── models/              ← Dart data classes for JSON parsing
│   │   ├── contract_analysis.dart
│   │   ├── vehicle_info.dart
│   │   └── price_estimate.dart
│   ├── services/
│   │   └── api_service.dart ← HTTP client for all backend calls
│   └── screens/
│       ├── dashboard_screen.dart  ← Home/summary screen
│       ├── analyze_screen.dart    ← PDF upload + results
│       ├── vin_screen.dart        ← VIN lookup
│       ├── price_screen.dart      ← Price estimation
│       ├── negotiation_screen.dart← Chat interface
│       └── results_screen.dart    ← Detailed analysis view
├── pubspec.yaml             ← Dependencies (http, file_picker, etc.)
└── android/ ios/ web/       ← Platform-specific code
```

---

## 9.2 Creating the Flutter Project

```bash
cd ~/Desktop/Infosys/CARChatbot

# Create Flutter project in the app/ directory
flutter create app
cd app
```

### Dependencies — `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0          # HTTP client for API calls
  file_picker: ^6.1.1    # Native file picker for PDF selection
  cupertino_icons: ^1.0.6
  google_fonts: ^6.1.0   # Modern typography
```

Install dependencies:
```bash
cd app
flutter pub get
```

---

## 9.3 API Service — Connecting to the Backend

### File: `app/lib/services/api_service.dart`

This is the **single entry point** for all backend communication. Every screen uses this service to make API calls.

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Change this to your server's IP for physical device testing
  static const String baseUrl = 'http://10.0.2.2:8000';
  // 10.0.2.2 = Android emulator → host machine's localhost
  // Use 'localhost' for web, your IP for physical devices

  // ──── Health Check ────
  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // ──── Contract Analysis ────
  static Future<Map<String, dynamic>> analyzeContract(File file) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/analyze'));
    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    var streamedResponse = await request.send()
        .timeout(const Duration(seconds: 120));  // LLM extraction takes time
    var response = await http.Response.fromStream(streamedResponse);
    return jsonDecode(response.body);
  }

  // ──── VIN Lookup ────
  static Future<Map<String, dynamic>> lookupVin(String vin) async {
    final response = await http.get(Uri.parse('$baseUrl/vin/$vin'))
        .timeout(const Duration(seconds: 30));
    return jsonDecode(response.body);
  }

  // ──── Price Estimate ────
  static Future<Map<String, dynamic>> estimatePrice({
    required String make,
    required String model,
    required int year,
    int? mileage,
    String condition = 'good',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/price-estimate'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'make': make, 'model': model, 'year': year,
        'mileage': mileage, 'condition': condition,
      }),
    );
    return jsonDecode(response.body);
  }

  // ──── Negotiation ────
  static Future<Map<String, dynamic>> startNegotiation(int contractId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/negotiate/start'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'contract_id': contractId}),
    );
    return jsonDecode(response.body);
  }

  static Future<Map<String, dynamic>> sendChatMessage(
      int threadId, String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/negotiate/chat'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'thread_id': threadId, 'message': message}),
    );
    return jsonDecode(response.body);
  }
}
```

**Key Design Decisions:**

| Decision | Reasoning |
|----------|-----------|
| `10.0.2.2` as base URL | Android emulator maps this to host's `localhost` |
| 120-second timeout for `/analyze` | LLM extraction can take 30–60 seconds on slower machines |
| Static methods | No instance state needed — pure utility class |
| `jsonDecode` everywhere | All backend responses are JSON |

---

## 9.4 Data Models

### File: `app/lib/models/contract_analysis.dart`

```dart
class ContractAnalysis {
  final int contractId;
  final Map<String, dynamic> sla;
  final Map<String, dynamic> fairness;
  final List<dynamic> negotiationPoints;
  final String extractionMethod;

  ContractAnalysis({
    required this.contractId,
    required this.sla,
    required this.fairness,
    required this.negotiationPoints,
    required this.extractionMethod,
  });

  factory ContractAnalysis.fromJson(Map<String, dynamic> json) {
    return ContractAnalysis(
      contractId: json['contract_id'] ?? 0,
      sla: json['sla'] ?? {},
      fairness: json['fairness'] ?? {},
      negotiationPoints: json['negotiation_points'] ?? [],
      extractionMethod: json['extraction_method'] ?? 'unknown',
    );
  }

  double get fairnessScore =>
      (fairness['fairness_score'] as num?)?.toDouble() ?? 0.0;

  String get rating => fairness['rating'] ?? 'Unknown';
}
```

---

## 9.5 Main App — Theme and Navigation

### File: `app/lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'screens/dashboard_screen.dart';
import 'screens/analyze_screen.dart';
import 'screens/vin_screen.dart';
import 'screens/price_screen.dart';

void main() => runApp(const CarContractApp());

class CarContractApp extends StatelessWidget {
  const CarContractApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Car Contract Advisor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF1565C0),  // Deep blue
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF42A5F5),
        brightness: Brightness.dark,
      ),
      themeMode: ThemeMode.system,
      home: const MainNavigation(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});
  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _selectedIndex = 0;

  static const List<Widget> _screens = [
    DashboardScreen(),
    AnalyzeScreen(),
    VinScreen(),
    PriceScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) => setState(() => _selectedIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.analytics), label: 'Analyze'),
          NavigationDestination(icon: Icon(Icons.directions_car), label: 'VIN'),
          NavigationDestination(icon: Icon(Icons.price_check), label: 'Price'),
        ],
      ),
    );
  }
}
```

---

## 9.6 Key Screens

### Analyze Screen (PDF Upload)

The analyze screen lets users:
1. Pick a PDF file using the native file picker
2. Upload it to the backend
3. View analysis results (SLA, fairness score, red flags)
4. Navigate to negotiation chat

```dart
// Key flow:
ElevatedButton(
  onPressed: () async {
    // 1. Pick PDF file
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );
    if (result == null) return;

    // 2. Upload to backend
    setState(() => _isLoading = true);
    final analysis = await ApiService.analyzeContract(
      File(result.files.single.path!)
    );

    // 3. Parse and display results
    setState(() {
      _analysis = ContractAnalysis.fromJson(analysis);
      _isLoading = false;
    });
  },
  child: Text('Upload Contract PDF'),
),
```

### VIN Screen

```dart
// VIN input with validation
TextField(
  controller: _vinController,
  maxLength: 17,
  decoration: InputDecoration(
    labelText: 'Vehicle Identification Number',
    hintText: '1HGCR2F38PA123456',
    prefixIcon: Icon(Icons.pin),
  ),
),
ElevatedButton(
  onPressed: () async {
    final result = await ApiService.lookupVin(_vinController.text);
    // Display vehicle info, recalls, complaints
  },
  child: Text('Decode VIN'),
),
```

### Negotiation Chat Screen

```dart
// Chat-like interface using ListView
ListView.builder(
  itemCount: _messages.length,
  itemBuilder: (context, index) {
    final msg = _messages[index];
    final isUser = msg['role'] == 'user';
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isUser ? Colors.blue[100] : Colors.grey[200],
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(msg['content']),
      ),
    );
  },
),
```

---

## 9.7 Running the Flutter App

```bash
cd app

# Run on connected device or emulator
flutter run

# Run on Chrome (web)
flutter run -d chrome

# Run on specific device
flutter devices          # List available devices
flutter run -d <device>  # Run on specific device
```

> **Important:** Make sure the FastAPI backend is running on port 8000 before starting the Flutter app.

---

[← Previous: FastAPI Backend](08-fastapi-backend.md) | [Back to Contents](../DOCUMENTATION.md) | [Next: Testing & Deployment →](10-testing-deployment.md)

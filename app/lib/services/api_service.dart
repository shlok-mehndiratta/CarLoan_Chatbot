import 'dart:async';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/contract_model.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();

  factory ApiService() {
    return _instance;
  }

  ApiService._internal();

  String get baseUrl => dotenv.env['API_URL'] ?? 'http://localhost:8000';

  // ──────────── Contract Analysis ──────────── //

  Future<ContractAnalysis> uploadAndAnalyzeContract(
    String filePath,
    String fileName,
  ) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/analyze'),
      );

      request.files.add(
        await http.MultipartFile.fromPath('file', filePath),
      );

      var streamedResponse = await request.send().timeout(
        const Duration(minutes: 5),
        onTimeout: () {
          throw TimeoutException('Upload timeout - Please try again');
        },
      );

      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);

        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }

        return ContractAnalysis.fromJson(json);
      } else {
        final errorJson = jsonDecode(response.body);
        throw Exception(errorJson['error'] ?? 'Upload failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  // ──────────── VIN Lookup ──────────── //

  Future<VehicleInfo> getVehicleInfo(String vin) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/vin/$vin'))
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return VehicleInfo.fromJson(json);
      } else {
        throw Exception('VIN lookup failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<Map<String, dynamic>> getVehicleDetails(String vin) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/vin/$vin'))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('VIN lookup failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  // ──────────── Price Estimation ──────────── //

  Future<PriceEstimate> estimatePrice({
    required String make,
    required String model,
    required int year,
    int? mileage,
    String condition = 'good',
  }) async {
    try {
      final body = {
        'make': make,
        'model': model,
        'year': year,
        'condition': condition,
      };
      if (mileage != null) body['mileage'] = mileage;

      final response = await http
          .post(
            Uri.parse('$baseUrl/price-estimate'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return PriceEstimate.fromJson(json);
      } else {
        throw Exception('Price estimation failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<PriceEstimate> estimatePriceByVin(String vin) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/price-estimate/$vin'))
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return PriceEstimate.fromJson(json);
      } else {
        throw Exception('VIN price estimation failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  // ──────────── Negotiation ──────────── //

  Future<NegotiationThread> startNegotiation(int contractId,
      {String? title}) async {
    try {
      final body = {'contract_id': contractId};
      if (title != null) body['title'] = title;

      final response = await http
          .post(
            Uri.parse('$baseUrl/negotiate/start'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return NegotiationThread.fromJson(json);
      } else {
        throw Exception('Failed to start negotiation');
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<String> sendNegotiationMessage(int threadId, String message) async {
    try {
      final response = await http
          .post(
            Uri.parse('$baseUrl/negotiate/chat'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'thread_id': threadId,
              'message': message,
            }),
          )
          .timeout(const Duration(minutes: 2));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return json['response'] ?? '';
      } else {
        throw Exception('Chat failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<List<ChatMessage>> getNegotiationHistory(int threadId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/negotiate/history/$threadId'))
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return (json['messages'] as List<dynamic>?)
                ?.map((m) => ChatMessage.fromJson(m))
                .toList() ??
            [];
      } else {
        throw Exception('Failed to load history');
      }
    } catch (e) {
      rethrow;
    }
  }

  Future<String> generateNegotiationEmail(
    int contractId, {
    List<String>? specificRequests,
    String tone = 'professional',
  }) async {
    try {
      final body = <String, dynamic>{
        'contract_id': contractId,
        'tone': tone,
      };
      if (specificRequests != null) {
        body['specific_requests'] = specificRequests;
      }

      final response = await http
          .post(
            Uri.parse('$baseUrl/negotiate/email'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(minutes: 2));

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        if (json.containsKey('error')) {
          throw Exception(json['error']);
        }
        return json['email'] ?? '';
      } else {
        throw Exception('Email generation failed');
      }
    } catch (e) {
      rethrow;
    }
  }

  // ──────────── Health ──────────── //

  Future<bool> checkHealth() async {
    try {
      final response =
          await http.get(Uri.parse('$baseUrl/health')).timeout(
        const Duration(seconds: 5),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
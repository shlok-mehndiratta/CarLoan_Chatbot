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

        return ContractAnalysis(
          contractId: json['contract_id'] ?? 0,
          fileName: fileName,
          sla: SLAData.fromJson(json['sla'] ?? {}),
          fairness: FairnessScore.fromJson(json['fairness'] ?? {}),
          analyzedAt: DateTime.now(),
        );
      } else {
        final errorJson = jsonDecode(response.body);
        throw Exception(errorJson['error'] ?? 'Upload failed');
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
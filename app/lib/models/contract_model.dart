import 'package:flutter/material.dart';

// ──────────────── Contract Analysis ──────────────── //

class ContractAnalysis {
  final int contractId;
  final String fileName;
  final SLAData sla;
  final FairnessScore fairness;
  final List<NegotiationPoint> negotiationPoints;
  final String? extractionMethod;
  final PriceComparison? priceComparison;
  final DateTime analyzedAt;

  ContractAnalysis({
    required this.contractId,
    required this.fileName,
    required this.sla,
    required this.fairness,
    this.negotiationPoints = const [],
    this.extractionMethod,
    this.priceComparison,
    required this.analyzedAt,
  });

  factory ContractAnalysis.fromJson(Map<String, dynamic> json) {
    return ContractAnalysis(
      contractId: json['contract_id'] ?? 0,
      fileName: json['file_name'] ?? 'Unknown',
      sla: SLAData.fromJson(json['sla'] ?? {}),
      fairness: FairnessScore.fromJson(json['fairness'] ?? {}),
      negotiationPoints: (json['negotiation_points'] as List<dynamic>?)
              ?.map((p) => NegotiationPoint.fromJson(p is Map<String, dynamic> ? p : {'point': p.toString()}))
              .toList() ??
          [],
      extractionMethod: json['extraction_method'],
      priceComparison: json['price_comparison'] != null
          ? PriceComparison.fromJson(json['price_comparison'])
          : null,
      analyzedAt: DateTime.now(),
    );
  }
}

class SLAData {
  final String? contractType;
  final double? interestRateApr;
  final int? leaseTermMonths;
  final double? monthlyPayment;
  final double? downPayment;
  final double? financeAmount;
  final double? residualValue;
  final int? mileageAllowance;
  final double? overageChargePerMile;
  final String? earlyTerminationClause;
  final double? purchaseOptionPrice;
  final String? maintenanceResponsibility;
  final String? warrantyInfo;
  final String? insuranceRequirements;
  final String? latePaymentPenalty;
  final Map<String, dynamic>? fees;
  final Map<String, dynamic>? penalties;
  final List<String> redFlags;

  SLAData({
    this.contractType,
    this.interestRateApr,
    this.leaseTermMonths,
    this.monthlyPayment,
    this.downPayment,
    this.financeAmount,
    this.residualValue,
    this.mileageAllowance,
    this.overageChargePerMile,
    this.earlyTerminationClause,
    this.purchaseOptionPrice,
    this.maintenanceResponsibility,
    this.warrantyInfo,
    this.insuranceRequirements,
    this.latePaymentPenalty,
    this.fees,
    this.penalties,
    this.redFlags = const [],
  });

  factory SLAData.fromJson(Map<String, dynamic> json) {
    return SLAData(
      contractType: json['contract_type'] ?? json['loan_type'],
      interestRateApr: _toDouble(json['interest_rate_apr'] ?? json['apr_percent']),
      leaseTermMonths: _toInt(json['lease_term_months'] ?? json['term_months']),
      monthlyPayment: _toDouble(json['monthly_payment']),
      downPayment: _toDouble(json['down_payment']),
      financeAmount: _toDouble(json['finance_amount']),
      residualValue: _toDouble(json['residual_value']),
      mileageAllowance: _toInt(json['mileage_allowance']),
      overageChargePerMile: _toDouble(json['overage_charge_per_mile']),
      earlyTerminationClause: json['early_termination_clause'],
      purchaseOptionPrice: _toDouble(json['purchase_option_price']),
      maintenanceResponsibility: json['maintenance_responsibility'],
      warrantyInfo: json['warranty_coverage'],
      insuranceRequirements: json['insurance_requirements'],
      latePaymentPenalty: json['late_payment_penalty'],
      fees: json['fees'] is Map ? Map<String, dynamic>.from(json['fees']) : null,
      penalties: json['penalties'] is Map ? Map<String, dynamic>.from(json['penalties']) : null,
      redFlags: List<String>.from(json['red_flags'] ?? []),
    );
  }
}

class FairnessScore {
  final double score;
  final String rating;
  final String summary;
  final List<String> reasons;

  FairnessScore({
    required this.score,
    required this.rating,
    required this.summary,
    this.reasons = const [],
  });

  factory FairnessScore.fromJson(Map<String, dynamic> json) {
    return FairnessScore(
      score: _toDouble(json['fairness_score'] ?? json['score']) ?? 0.0,
      rating: json['rating'] ?? 'Unknown',
      summary: json['summary'] ?? '',
      reasons: List<String>.from(json['reasons'] ?? []),
    );
  }

  Color getScoreColor() {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.red;
  }
}

// ──────────────── Negotiation ──────────────── //

class NegotiationPoint {
  final String category;
  final String severity;
  final String point;
  final String? strategy;

  NegotiationPoint({
    required this.category,
    required this.severity,
    required this.point,
    this.strategy,
  });

  factory NegotiationPoint.fromJson(Map<String, dynamic> json) {
    return NegotiationPoint(
      category: json['category'] ?? 'general',
      severity: json['severity'] ?? 'medium',
      point: json['point'] ?? json.toString(),
      strategy: json['strategy'],
    );
  }

  Color getSeverityColor() {
    switch (severity) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  IconData getSeverityIcon() {
    switch (severity) {
      case 'high':
        return Icons.warning;
      case 'medium':
        return Icons.info;
      default:
        return Icons.check_circle;
    }
  }
}

class NegotiationThread {
  final int threadId;
  final int contractId;
  final String welcomeMessage;
  final List<NegotiationPoint> negotiationPoints;
  final FairnessScore? fairness;

  NegotiationThread({
    required this.threadId,
    required this.contractId,
    required this.welcomeMessage,
    this.negotiationPoints = const [],
    this.fairness,
  });

  factory NegotiationThread.fromJson(Map<String, dynamic> json) {
    return NegotiationThread(
      threadId: json['thread_id'] ?? 0,
      contractId: json['contract_id'] ?? 0,
      welcomeMessage: json['welcome_message'] ?? '',
      negotiationPoints: (json['negotiation_points'] as List<dynamic>?)
              ?.map((p) => NegotiationPoint.fromJson(p is Map<String, dynamic> ? p : {'point': p.toString()}))
              .toList() ??
          [],
      fairness: json['fairness'] != null
          ? FairnessScore.fromJson(json['fairness'])
          : null,
    );
  }
}

class ChatMessage {
  final String role;
  final String content;
  final String? createdAt;

  ChatMessage({
    required this.role,
    required this.content,
    this.createdAt,
  });

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      role: json['role'] ?? 'user',
      content: json['content'] ?? '',
      createdAt: json['created_at'],
    );
  }
}

// ──────────────── Vehicle & VIN ──────────────── //

class VehicleInfo {
  final String vin;
  final String? make;
  final String? model;
  final String? year;
  final String? bodyClass;
  final String? engineType;
  final String? fuelType;
  final String? driveType;
  final String? transmission;
  final String? trim;
  final String? manufacturer;
  final int? cylinders;
  final List<RecallInfo> recalls;
  final int complaintsCount;

  VehicleInfo({
    required this.vin,
    this.make,
    this.model,
    this.year,
    this.bodyClass,
    this.engineType,
    this.fuelType,
    this.driveType,
    this.transmission,
    this.trim,
    this.manufacturer,
    this.cylinders,
    this.recalls = const [],
    this.complaintsCount = 0,
  });

  factory VehicleInfo.fromJson(Map<String, dynamic> json) {
    final vehicle = json['vehicle'] ?? json;
    return VehicleInfo(
      vin: vehicle['vin'] ?? '',
      make: vehicle['make'],
      model: vehicle['model'],
      year: vehicle['year']?.toString(),
      bodyClass: vehicle['body_class'],
      engineType: vehicle['engine_type'],
      fuelType: vehicle['fuel_type'],
      driveType: vehicle['drive_type'],
      transmission: vehicle['transmission'],
      trim: vehicle['trim'],
      manufacturer: vehicle['manufacturer'],
      cylinders: _toInt(vehicle['cylinders']),
      recalls: (json['recalls'] as List<dynamic>?)
              ?.map((r) => RecallInfo.fromJson(r))
              .toList() ??
          [],
      complaintsCount: json['complaints_count'] ?? 0,
    );
  }
}

class RecallInfo {
  final String campaignNumber;
  final String component;
  final String summary;
  final String? consequence;
  final String? remedy;

  RecallInfo({
    required this.campaignNumber,
    required this.component,
    required this.summary,
    this.consequence,
    this.remedy,
  });

  factory RecallInfo.fromJson(Map<String, dynamic> json) {
    return RecallInfo(
      campaignNumber: json['campaign_number'] ?? '',
      component: json['component'] ?? '',
      summary: json['summary'] ?? '',
      consequence: json['consequence'],
      remedy: json['remedy'],
    );
  }
}

// ──────────────── Price Estimation ──────────────── //

class PriceEstimate {
  final String? make;
  final String? model;
  final int? year;
  final int? mileage;
  final String? condition;
  final double? lowPrice;
  final double? marketPrice;
  final double? highPrice;
  final double? msrp;
  final double? confidence;
  final String? source;
  final List<String> notes;
  final String? vin;

  PriceEstimate({
    this.make,
    this.model,
    this.year,
    this.mileage,
    this.condition,
    this.lowPrice,
    this.marketPrice,
    this.highPrice,
    this.msrp,
    this.confidence,
    this.source,
    this.notes = const [],
    this.vin,
  });

  factory PriceEstimate.fromJson(Map<String, dynamic> json) {
    return PriceEstimate(
      make: json['make'],
      model: json['model'],
      year: _toInt(json['year']),
      mileage: _toInt(json['mileage']),
      condition: json['condition'],
      lowPrice: _toDouble(json['low_price']),
      marketPrice: _toDouble(json['market_price']),
      highPrice: _toDouble(json['high_price']),
      msrp: _toDouble(json['msrp']),
      confidence: _toDouble(json['confidence']),
      source: json['source'],
      notes: List<String>.from(json['notes'] ?? []),
      vin: json['vin'],
    );
  }
}

class PriceComparison {
  final bool comparisonAvailable;
  final String? assessment;
  final double? deviationPercent;
  final String? message;
  final String? priceRange;

  PriceComparison({
    required this.comparisonAvailable,
    this.assessment,
    this.deviationPercent,
    this.message,
    this.priceRange,
  });

  factory PriceComparison.fromJson(Map<String, dynamic> json) {
    return PriceComparison(
      comparisonAvailable: json['comparison_available'] ?? false,
      assessment: json['assessment'],
      deviationPercent: _toDouble(json['deviation_percent']),
      message: json['message'],
      priceRange: json['price_range'],
    );
  }
}

// ──────────────── Helpers ──────────────── //

double? _toDouble(dynamic value) {
  if (value == null) return null;
  if (value is double) return value;
  if (value is int) return value.toDouble();
  if (value is String) return double.tryParse(value);
  return null;
}

int? _toInt(dynamic value) {
  if (value == null) return null;
  if (value is int) return value;
  if (value is double) return value.toInt();
  if (value is String) return int.tryParse(value);
  return null;
}
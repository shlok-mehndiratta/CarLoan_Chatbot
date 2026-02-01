import 'package:flutter/material.dart';

class ContractAnalysis {
  final int contractId;
  final String fileName;
  final SLAData sla;
  final FairnessScore fairness;
  final DateTime analyzedAt;

  ContractAnalysis({
    required this.contractId,
    required this.fileName,
    required this.sla,
    required this.fairness,
    required this.analyzedAt,
  });

  factory ContractAnalysis.fromJson(Map<String, dynamic> json) {
    return ContractAnalysis(
      contractId: json['contract_id'] ?? 0,
      fileName: json['file_name'] ?? 'Unknown',
      sla: SLAData.fromJson(json['sla'] ?? {}),
      fairness: FairnessScore.fromJson(json['fairness'] ?? {}),
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
  final double? residualValue;
  final int? mileageAllowance;
  final double? overageChargePerMile;
  final String? earlyTerminationClause;
  final double? purchaseOptionPrice;
  final String? maintenanceResponsibility;
  final String? warrantyInfo;
  final String? insuranceRequirements;
  final String? latePaymentPenalty;
  final List<String> redFlags;

  SLAData({
    this.contractType,
    this.interestRateApr,
    this.leaseTermMonths,
    this.monthlyPayment,
    this.downPayment,
    this.residualValue,
    this.mileageAllowance,
    this.overageChargePerMile,
    this.earlyTerminationClause,
    this.purchaseOptionPrice,
    this.maintenanceResponsibility,
    this.warrantyInfo,
    this.insuranceRequirements,
    this.latePaymentPenalty,
    this.redFlags = const [],
  });

  factory SLAData.fromJson(Map<String, dynamic> json) {
    return SLAData(
      contractType: json['contract_type'],
      interestRateApr: (json['interest_rate_apr'] as num?)?.toDouble(),
      leaseTermMonths: json['lease_term_months'],
      monthlyPayment: (json['monthly_payment'] as num?)?.toDouble(),
      downPayment: (json['down_payment'] as num?)?.toDouble(),
      residualValue: (json['residual_value'] as num?)?.toDouble(),
      mileageAllowance: json['mileage_allowance'],
      overageChargePerMile: (json['overage_charge_per_mile'] as num?)?.toDouble(),
      earlyTerminationClause: json['early_termination_clause'],
      purchaseOptionPrice: (json['purchase_option_price'] as num?)?.toDouble(),
      maintenanceResponsibility: json['maintenance_responsibility'],
      warrantyInfo: json['warranty_coverage'],
      insuranceRequirements: json['insurance_requirements'],
      latePaymentPenalty: json['late_payment_penalty'],
      redFlags: List<String>.from(json['red_flags'] ?? []),
    );
  }
}

class FairnessScore {
  final double score;
  final String rating;
  final String summary;

  FairnessScore({
    required this.score,
    required this.rating,
    required this.summary,
  });

  factory FairnessScore.fromJson(Map<String, dynamic> json) {
    return FairnessScore(
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      rating: json['rating'] ?? 'Unknown',
      summary: json['summary'] ?? '',
    );
  }

  Color getScoreColor() {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.red;
  }
}
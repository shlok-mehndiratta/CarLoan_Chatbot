import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/contract_model.dart';

class ResultScreen extends StatelessWidget {
  final ContractAnalysis analysis;

  const ResultScreen({
    super.key,
    required this.analysis,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Results'),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Fairness Score Card
            Container(
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: analysis.fairness.getScoreColor().withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: analysis.fairness.getScoreColor(),
                  width: 2,
                ),
              ),
              child: Column(
                children: [
                  Text(
                    'Fairness Score',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${analysis.fairness.score.toStringAsFixed(1)}%',
                    style: TextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.bold,
                      color: analysis.fairness.getScoreColor(),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    analysis.fairness.rating,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                      color: analysis.fairness.getScoreColor(),
                    ),
                  ),
                  if (analysis.fairness.summary.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text(
                      analysis.fairness.summary,
                      textAlign: TextAlign.center,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ],
              ),
            ),

            // Red Flags
            if (analysis.sla.redFlags.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '⚠️ Red Flags',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ...analysis.sla.redFlags.map(
                      (flag) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.red.shade200),
                          ),
                          child: Text(flag),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),

            // SLA Details
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Contract Details',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildDetailCard(context, 'Contract Type', analysis.sla.contractType),
                  _buildDetailCard(context, 'Interest Rate (APR)', analysis.sla.interestRateApr != null ? '${analysis.sla.interestRateApr}%' : null),
                  _buildDetailCard(context, 'Lease Term', analysis.sla.leaseTermMonths != null ? '${analysis.sla.leaseTermMonths} months' : null),
                  _buildDetailCard(context, 'Monthly Payment', analysis.sla.monthlyPayment != null ? '\$${analysis.sla.monthlyPayment!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Down Payment', analysis.sla.downPayment != null ? '\$${analysis.sla.downPayment!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Mileage Allowance', analysis.sla.mileageAllowance != null ? '${analysis.sla.mileageAllowance} miles/year' : null),
                  _buildDetailCard(context, 'Overage Charge', analysis.sla.overageChargePerMile != null ? '\$${analysis.sla.overageChargePerMile}/mile' : null),
                  _buildDetailCard(context, 'Residual Value', analysis.sla.residualValue != null ? '\$${analysis.sla.residualValue!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Warranty Coverage', analysis.sla.warrantyInfo),
                  _buildDetailCard(context, 'Maintenance', analysis.sla.maintenanceResponsibility),
                  _buildDetailCard(context, 'Insurance Requirements', analysis.sla.insuranceRequirements),
                  _buildDetailCard(context, 'Early Termination', analysis.sla.earlyTerminationClause),
                  _buildDetailCard(context, 'Late Payment Penalty', analysis.sla.latePaymentPenalty),
                  const SizedBox(height: 16),
                ],
              ),
            ),

            // Action Buttons
            Padding(
              padding: const EdgeInsets.all(16),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                  child: const Text('Analyze Another Contract'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailCard(BuildContext context, String label, String? value) {
    if (value == null || value.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.grey.shade50,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey.shade200),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 13,
              ),
            ),
            Expanded(
              child: Text(
                value,
                textAlign: TextAlign.right,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).primaryColor,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
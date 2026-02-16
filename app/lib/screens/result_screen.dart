import 'package:flutter/material.dart';
import '../models/contract_model.dart';
import 'negotiation_chat_screen.dart';

class ResultScreen extends StatelessWidget {
  final ContractAnalysis analysis;

  const ResultScreen({
    super.key,
    required this.analysis,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: analysis.fairness.getScoreColor(),
                  width: 2,
                ),
              ),
              child: Column(
                children: [
                  Text('Fairness Score', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 12),
                  Text(
                    '${analysis.fairness.score.toStringAsFixed(0)}',
                    style: TextStyle(
                      fontSize: 52,
                      fontWeight: FontWeight.bold,
                      color: analysis.fairness.getScoreColor(),
                    ),
                  ),
                  Text(
                    'out of 100',
                    style: TextStyle(fontSize: 14, color: Colors.grey.shade600),
                  ),
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                    decoration: BoxDecoration(
                      color: analysis.fairness.getScoreColor().withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      analysis.fairness.rating,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: analysis.fairness.getScoreColor(),
                      ),
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

            // Fairness reasons
            if (analysis.fairness.reasons.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Score Breakdown',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    ...analysis.fairness.reasons.map((reason) => Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.info_outline, size: 16, color: Colors.grey.shade600),
                          const SizedBox(width: 8),
                          Expanded(child: Text(reason, style: const TextStyle(fontSize: 13))),
                        ],
                      ),
                    )),
                    const SizedBox(height: 16),
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
                      style: theme.textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    ),
                    const SizedBox(height: 8),
                    ...analysis.sla.redFlags.map(
                      (flag) => Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Container(
                          width: double.infinity,
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
                    const SizedBox(height: 16),
                  ],
                ),
              ),

            // Negotiation Points
            if (analysis.negotiationPoints.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '💡 Negotiation Points',
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    ...analysis.negotiationPoints.map((p) => Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      child: ListTile(
                        leading: Icon(p.getSeverityIcon(), color: p.getSeverityColor()),
                        title: Text(p.point, style: const TextStyle(fontSize: 13)),
                        subtitle: p.strategy != null
                            ? Text(p.strategy!, style: TextStyle(fontSize: 12, color: Colors.grey.shade600))
                            : null,
                      ),
                    )),
                    const SizedBox(height: 16),
                  ],
                ),
              ),

            // Contract Details
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Contract Details',
                    style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 12),
                  _buildDetailCard(context, 'Contract Type', analysis.sla.contractType),
                  _buildDetailCard(context, 'Interest Rate (APR)', analysis.sla.interestRateApr != null ? '${analysis.sla.interestRateApr}%' : null),
                  _buildDetailCard(context, 'Lease Term', analysis.sla.leaseTermMonths != null ? '${analysis.sla.leaseTermMonths} months' : null),
                  _buildDetailCard(context, 'Monthly Payment', analysis.sla.monthlyPayment != null ? '\$${analysis.sla.monthlyPayment!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Down Payment', analysis.sla.downPayment != null ? '\$${analysis.sla.downPayment!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Finance Amount', analysis.sla.financeAmount != null ? '\$${analysis.sla.financeAmount!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Mileage Allowance', analysis.sla.mileageAllowance != null ? '${analysis.sla.mileageAllowance} miles/year' : null),
                  _buildDetailCard(context, 'Residual Value', analysis.sla.residualValue != null ? '\$${analysis.sla.residualValue!.toStringAsFixed(2)}' : null),
                  _buildDetailCard(context, 'Warranty Coverage', analysis.sla.warrantyInfo),
                  _buildDetailCard(context, 'Maintenance', analysis.sla.maintenanceResponsibility),
                  _buildDetailCard(context, 'Insurance Requirements', analysis.sla.insuranceRequirements),
                  _buildDetailCard(context, 'Early Termination', analysis.sla.earlyTerminationClause),
                  _buildDetailCard(context, 'Late Payment Penalty', analysis.sla.latePaymentPenalty),
                  _buildDetailCard(context, 'Extraction Method', analysis.extractionMethod),
                  const SizedBox(height: 16),
                ],
              ),
            ),

            // Price Comparison
            if (analysis.priceComparison != null && analysis.priceComparison!.comparisonAvailable)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Card(
                  color: Colors.green.shade50,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.attach_money, color: Colors.green),
                            const SizedBox(width: 8),
                            Text('Price Comparison', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                          ],
                        ),
                        const SizedBox(height: 8),
                        if (analysis.priceComparison!.message != null)
                          Text(analysis.priceComparison!.message!),
                        if (analysis.priceComparison!.priceRange != null)
                          Text('Market Range: ${analysis.priceComparison!.priceRange}',
                              style: const TextStyle(fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ),
              ),

            const SizedBox(height: 16),

            // Action Buttons
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => NegotiationChatScreen(
                              contractId: analysis.contractId,
                              contractName: analysis.fileName,
                            ),
                          ),
                        );
                      },
                      icon: const Icon(Icons.chat),
                      label: const Text('Start Negotiation Chat'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: theme.primaryColor,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                      icon: const Icon(Icons.add),
                      label: const Text('Analyze Another Contract'),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                ],
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
      padding: const EdgeInsets.only(bottom: 10),
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
              style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
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
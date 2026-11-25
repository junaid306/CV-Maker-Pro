import 'package:flutter/material.dart';

import '../../services/services.dart';
import '../../widgets/common_widgets.dart';
import '../../widgets/theme.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final email = TextEditingController();
  bool loading = false;
  bool sent = false;
  String? error;

  Future<void> submit() async {
    setState(() {
      loading = true;
      error = null;
    });
    try {
      await AuthService.instance.forgotPassword(email.text.trim());
      setState(() => sent = true);
    } catch (e) {
      setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot password')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(
            'Enter your account email. If the email exists, we will send reset instructions.',
            style: TextStyle(color: AppColors.muted, fontSize: 13),
          ),
          const SizedBox(height: 16),
          AppTextField(controller: email, label: 'Email', keyboardType: TextInputType.emailAddress),
          if (error != null) ...[
            const SizedBox(height: 12),
            Text(error!, style: const TextStyle(color: AppColors.danger, fontSize: 13)),
          ],
          if (sent) ...[
            const SizedBox(height: 12),
            const Text(
              'If the email exists, a reset code has been sent.',
              style: TextStyle(color: AppColors.primary, fontSize: 13),
            ),
          ],
          const SizedBox(height: 20),
          PrimaryButton(label: 'Send reset code', onPressed: submit, loading: loading),
        ],
      ),
    );
  }
}

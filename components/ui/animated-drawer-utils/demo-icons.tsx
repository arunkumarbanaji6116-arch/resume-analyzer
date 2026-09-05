import React from "react";
import {
  Ban,
  AlertTriangle,
  ScanFace,
  Lock,
  Key,
  FileText,
  KeyRound,
  Shield,
  AlertCircle
} from "lucide-react";

export const BannedIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <Ban className="w-5 h-5 text-neutral-500" {...(props as any)} />
);

export const DangerIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <AlertCircle className="w-6 h-6 text-red-500" {...(props as any)} />
);

export const FaceIDIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <ScanFace className="w-5 h-5" {...(props as any)} />
);

export const LockIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <Lock className="w-5 h-5 text-neutral-600 dark:text-neutral-400" {...(props as any)} />
);

export const PassIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <Key className="w-5 h-5 text-neutral-600 dark:text-neutral-400" {...(props as any)} />
);

export const PhraseIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <FileText className="w-5 h-5 text-neutral-500" {...(props as any)} />
);

export const RecoveryPhraseIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <KeyRound className="w-6 h-6 text-sky-500" {...(props as any)} />
);

export const ShieldIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <Shield className="w-5 h-5 text-neutral-500" {...(props as any)} />
);

export const WarningIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <AlertTriangle className="w-5 h-5 text-red-500" {...(props as any)} />
);

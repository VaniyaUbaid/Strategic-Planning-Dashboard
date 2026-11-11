import React from "react";
import { Loader2 } from "lucide-react";

export default function LoadingSpinner({ message = "Loading data..." }) {
  return (
    <div className="loading-box">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600" size={32} />
      <p className="font-medium text-slate-600">{message}</p>
    </div>
  );
}

import { Loader2 } from 'lucide-react';

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <Loader2 
          className="h-12 w-12 animate-spin mx-auto mb-4" 
          style={{ color: '#00A3E0' }}
        />
        <p style={{ color: '#4B5563', fontFamily: 'Poppins', fontWeight: 400 }}>
          Loading error data...
        </p>
      </div>
    </div>
  );
}
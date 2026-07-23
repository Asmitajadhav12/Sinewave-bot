import { ChevronRight } from 'lucide-react';
import { Card } from './ui/card';

export interface Product {
  id: string;
  name: string;
  description: string;
}

interface ProductSelectionProps {
  onProductSelect: (productId: string) => void;
}

const products: Product[] = [
  {
    id: 'taxbase',
    name: 'Taxbase',
    description: 'Comprehensive tax management solution',
  },
  {
    id: 'gstpro',
    name: 'GSTPro',
    description: 'GST compliance and filing platform',
  },
  {
    id: 'tdspro',
    name: 'TDSPro',
    description: 'TDS return filing and management',
  },
  {
    id: 'taxbase-cloud',
    name: 'Taxbase Cloud',
    description: 'Cloud-based tax solution',
  },
];

export function ProductSelection({ onProductSelect }: ProductSelectionProps) {
  return (
    <div className="min-h-[calc(100vh-200px)] flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        <h2 
          className="text-2xl mb-8 text-center"
          style={{ 
            color: '#1F2937', 
            fontFamily: 'Poppins, sans-serif', 
            fontWeight: 600 
          }}
        >
          Select a Product
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {products.map((product) => (
            <Card
              key={product.id}
              className="p-6 cursor-pointer transition-all border-2 hover:shadow-lg"
              style={{ 
                borderColor: '#E5E7EB',
                backgroundColor: '#FFFFFF'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#00A3E0';
                e.currentTarget.style.backgroundColor = '#EAF7FD';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#E5E7EB';
                e.currentTarget.style.backgroundColor = '#FFFFFF';
              }}
              onClick={() => onProductSelect(product.id)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 
                    className="text-lg mb-2"
                    style={{ 
                      color: '#00A3E0', 
                      fontFamily: 'Poppins', 
                      fontWeight: 600 
                    }}
                  >
                    {product.name}
                  </h3>
                  <p 
                    className="text-sm"
                    style={{ 
                      color: '#4B5563', 
                      fontFamily: 'Poppins', 
                      fontWeight: 400 
                    }}
                  >
                    {product.description}
                  </p>
                </div>
                <ChevronRight 
                  className="h-6 w-6 flex-shrink-0"
                  style={{ color: '#00A3E0' }}
                />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

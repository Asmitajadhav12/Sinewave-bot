import { Database } from 'lucide-react';

export interface Product {
  id: number;
  name: string;
}

interface ProductSidebarProps {
  products: Product[];
  selectedProductId: number | null;
  onProductSelect: (productId: number) => void;
}

export function ProductSidebar({
  products,
  selectedProductId,
  onProductSelect,
}: ProductSidebarProps) {
  return (
    <aside
      className="w-64 border-r flex-shrink-0 overflow-y-auto"
      style={{
        backgroundColor: '#F9FAFB',
        borderColor: '#E5E7EB',
        minHeight: 'calc(100vh - 64px)',
        fontFamily: 'Poppins, sans-serif',
      }}
    >
      <div className="p-4">
        {/* Heading */}
        <h3
          className="mb-4 flex items-center gap-2 px-2"
          style={{
            color: '#2a7fc9',
            fontWeight: 700,
            fontSize: '17px',
            letterSpacing: '0.6px',
          }}
        >
          <Database className="h-4 w-4" style={{ color: '#0a87b4' }} />
          Products
        </h3>

        {/* Product List */}
        <div className="space-y-2">
          {Array.isArray(products) && products.map((product) => (
            <button
              key={product.id}
              onClick={() => onProductSelect(product.id)}
              className="w-full text-left rounded-lg border"
              style={{
                padding: '14px 16px',
                backgroundColor:
                  selectedProductId === product.id ? '#00A3E0' : '#FFFFFF',
                borderColor:
                  selectedProductId === product.id ? '#00A3E0' : '#E5E7EB',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow:
                  selectedProductId === product.id
                    ? '0 10px 24px rgba(0,163,224,0.35)'
                    : '0 2px 6px rgba(29, 27, 27, 0.06)',
              }}
              onMouseEnter={(e) => {
                if (selectedProductId !== product.id) {
                  e.currentTarget.style.backgroundColor = '#F0FAFF';
                  e.currentTarget.style.borderColor = '#00A3E0';
                  e.currentTarget.style.boxShadow =
                    '0 8px 18px rgba(0,163,224,0.25)';
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedProductId !== product.id) {
                  e.currentTarget.style.backgroundColor = '#FFFFFF';
                  e.currentTarget.style.borderColor = '#E5E7EB';
                  e.currentTarget.style.boxShadow =
                    '0 2px 6px rgba(0,0,0,0.06)';
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {/* Product Name */}
              <span
                style={{
                  color:
                    selectedProductId === product.id
                      ? '#FFFFFF'
                      : '#111827',
                  fontWeight:
                    selectedProductId === product.id ? 700 : 600,
                  fontSize: '14.5px',
                  lineHeight: '22px',
                  letterSpacing: '0.2px',
                }}
              >
                {product.name}
              </span>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}

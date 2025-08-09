import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useTheme } from '@mui/material/styles';

const AnalyticsChart = ({ type, data, title, height = 300 }) => {
  const theme = useTheme();
  
  const colors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main,
    theme.palette.info.main
  ];

  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="total_hours" 
                stroke={colors[0]} 
                name="Total Hours"
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="approved_count" 
                stroke={colors[2]} 
                name="Approved"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_hours" fill={colors[0]} name="Total Hours" />
              <Bar dataKey="submitted_count" fill={colors[1]} name="Submitted" />
              <Bar dataKey="approved_count" fill={colors[2]} name="Approved" />
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'team-bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_hours" fill={colors[0]} name="Total Hours" />
              <Bar dataKey="pending_count" fill={colors[3]} name="Pending" />
              <Bar dataKey="approved_count" fill={colors[2]} name="Approved" />
              <Bar dataKey="active_staff" fill={colors[5]} name="Active Staff" />
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );
      
      case 'staff-bar':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart data={data} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="staff_name" type="category" width={120} />
              <Tooltip />
              <Legend />
              <Bar dataKey="total_hours" fill={colors[0]} name="Total Hours" />
              <Bar dataKey="current_month_hours" fill={colors[1]} name="This Month" />
            </BarChart>
          </ResponsiveContainer>
        );
      
      default:
        return <div>Chart type not supported</div>;
    }
  };

  return renderChart();
};

export default AnalyticsChart;
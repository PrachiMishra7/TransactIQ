"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2, Shield } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { listRules, createRule, updateRule, deleteRule } from "@/lib/api";
import { toast } from "@/components/ui/toast";

interface Rule {
  id: string;
  country_name: string;
  country_code: string;
  field_name: string;
  validation_type: string;
  rule_value: string;
  is_active: boolean;
  version: number;
}

export default function RulesPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Rule | null>(null);
  const [form, setForm] = useState({
    country_name: "", country_code: "", field_name: "phone",
    validation_type: "phone_length", rule_value: "10", is_active: true,
  });

  const { data: rules, isLoading } = useQuery({ queryKey: ["rules"], queryFn: listRules });

  const createMut = useMutation({
    mutationFn: createRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
      toast("Rule created successfully", "success");
      setShowForm(false);
      resetForm();
    },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) => updateRule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
      toast("Rule updated successfully", "success");
      setEditing(null);
      resetForm();
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
      toast("Rule disabled", "success");
    },
  });

  const resetForm = () => setForm({ country_name: "", country_code: "", field_name: "phone", validation_type: "phone_length", rule_value: "10", is_active: true });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editing) {
      updateMut.mutate({ id: editing.id, data: form });
    } else {
      createMut.mutate(form);
    }
  };

  const startEdit = (rule: Rule) => {
    setEditing(rule);
    setForm({
      country_name: rule.country_name,
      country_code: rule.country_code,
      field_name: rule.field_name,
      validation_type: rule.validation_type,
      rule_value: rule.rule_value,
      is_active: rule.is_active,
    });
    setShowForm(true);
  };

  return (
    <DashboardLayout title="Validation Rules" description="Configure validation rules without code changes">
      <div className="mb-6 flex justify-between">
        <p className="text-sm text-slate-500">Admin-configurable rules with versioning support</p>
        <Button onClick={() => { setShowForm(true); setEditing(null); resetForm(); }}>
          <Plus className="h-4 w-4" /> Add Rule
        </Button>
      </div>

      {showForm && (
        <Card className="mb-6">
          <CardHeader><CardTitle>{editing ? "Edit Rule" : "Create New Rule"}</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div><Label>Country</Label><Input value={form.country_name} onChange={e => setForm(f => ({ ...f, country_name: e.target.value }))} required /></div>
              <div><Label>Country Code</Label><Input value={form.country_code} onChange={e => setForm(f => ({ ...f, country_code: e.target.value }))} placeholder="+91" /></div>
              <div><Label>Field</Label>
                <Select value={form.field_name} onChange={e => setForm(f => ({ ...f, field_name: e.target.value }))}>
                  <option value="phone">Phone</option>
                  <option value="email">Email</option>
                  <option value="payment_method">Payment Method</option>
                  <option value="order_date">Order Date</option>
                </Select>
              </div>
              <div><Label>Rule Type</Label>
                <Select value={form.validation_type} onChange={e => setForm(f => ({ ...f, validation_type: e.target.value }))}>
                  <option value="phone_length">Phone Length</option>
                  <option value="email_format">Email Format</option>
                  <option value="enum">Enum</option>
                  <option value="date_format">Date Format</option>
                </Select>
              </div>
              <div><Label>Rule Value</Label><Input value={form.rule_value} onChange={e => setForm(f => ({ ...f, rule_value: e.target.value }))} required /></div>
              <div className="flex items-end gap-2">
                <Button type="submit">{editing ? "Update" : "Create"}</Button>
                <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditing(null); }}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Shield className="h-5 w-5" /> Active Rules</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-center text-slate-400 py-8">Loading...</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-slate-50">
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Country</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Code</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Field</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Value</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Version</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rules?.map((rule: Rule) => (
                  <tr key={rule.id} className="border-b border-slate-100">
                    <td className="px-4 py-3 font-medium">{rule.country_name}</td>
                    <td className="px-4 py-3">{rule.country_code}</td>
                    <td className="px-4 py-3">{rule.field_name}</td>
                    <td className="px-4 py-3">{rule.validation_type}</td>
                    <td className="px-4 py-3 font-mono text-xs">{rule.rule_value}</td>
                    <td className="px-4 py-3">v{rule.version}</td>
                    <td className="px-4 py-3">
                      <Badge variant={rule.is_active ? "success" : "secondary"}>
                        {rule.is_active ? "Active" : "Disabled"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <Button variant="ghost" size="sm" onClick={() => startEdit(rule)}><Pencil className="h-4 w-4" /></Button>
                        {rule.is_active && (
                          <Button variant="ghost" size="sm" onClick={() => deleteMut.mutate(rule.id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </DashboardLayout>
  );
}

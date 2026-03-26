import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

function TaskSidebar({
  tasks,
  selectedTaskId,
  onSelectTask,
  categories,
  skills,
  onCreateTask,
}) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    category_id: "",
    selected_skill_ids: [],
    document_name: "",
    document_content: "",
  });

  useEffect(() => {
    if (!form.category_id && categories.length) {
      setForm((prev) => ({ ...prev, category_id: categories[0].id }));
    }
  }, [categories, form.category_id]);

  const candidateSkills = useMemo(() => {
    if (!form.category_id) return skills;
    return skills.filter(
      (item) =>
        item.category_bindings.length === 0 ||
        item.category_bindings.includes(form.category_id)
    );
  }, [skills, form.category_id]);

  function toggleSkill(skillId, checked) {
    setForm((prev) => {
      const next = new Set(prev.selected_skill_ids);
      if (checked) next.add(skillId);
      else next.delete(skillId);
      return { ...prev, selected_skill_ids: Array.from(next) };
    });
  }

  async function submit(event) {
    event.preventDefault();
    await onCreateTask(form);
    setForm({
      name: "",
      description: "",
      category_id: categories[0]?.id || "",
      selected_skill_ids: [],
      document_name: "",
      document_content: "",
    });
    setOpen(false);
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h3>Tasks</h3>
        <button className="btn" onClick={() => setOpen((v) => !v)}>
          {open ? "Close" : "New Task"}
        </button>
      </div>
      {open && (
        <form className="panel form-panel" onSubmit={submit}>
          <input
            placeholder="Task Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <textarea
            placeholder="Task Description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={3}
          />
          <select
            value={form.category_id}
            onChange={(e) => setForm({ ...form, category_id: e.target.value })}
          >
            {categories.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <input
            placeholder="Document Name"
            value={form.document_name}
            onChange={(e) => setForm({ ...form, document_name: e.target.value })}
          />
          <textarea
            placeholder="Document Content"
            value={form.document_content}
            onChange={(e) => setForm({ ...form, document_content: e.target.value })}
            rows={3}
          />
          <div className="checklist">
            {candidateSkills.map((skill) => (
              <label key={skill.id}>
                <input
                  type="checkbox"
                  checked={form.selected_skill_ids.includes(skill.id)}
                  onChange={(e) => toggleSkill(skill.id, e.target.checked)}
                />
                {skill.name}
              </label>
            ))}
          </div>
          <button className="btn" type="submit">
            Create Task
          </button>
        </form>
      )}
      {tasks.map((task) => (
        <div
          key={task.id}
          className={`task-card ${task.id === selectedTaskId ? "active" : ""}`}
          onClick={() => onSelectTask(task.id)}
        >
          <div className="task-name">{task.name}</div>
          <div className="task-desc">{task.description}</div>
        </div>
      ))}
    </aside>
  );
}

function ChatPage({ selectedTask, messages, onSend }) {
  const [input, setInput] = useState("");
  return (
    <div className="panel page-panel">
      <h3>{selectedTask ? selectedTask.name : "Select a Task"}</h3>
      <div className="tags">
        {(selectedTask?.selected_skill_ids || []).map((item) => (
          <span key={item} className="tag">
            {item}
          </span>
        ))}
      </div>
      <div className="chat-box">
        {messages.map((item) => (
          <div key={item.id} className={`message ${item.source}`}>
            <div className="message-meta">
              {item.role} / {item.source}
            </div>
            <div>{item.content}</div>
          </div>
        ))}
      </div>
      <div className="chat-send">
        <textarea
          rows={3}
          placeholder="Send message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          className="btn"
          onClick={async () => {
            if (!input.trim() || !selectedTask) return;
            await onSend(input);
            setInput("");
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

function SkillLibraryPage({ skills, categories, onUpdateSkill, onUpdateCategory }) {
  const groups = ["built_in", "platform_enhanced", "platform_new", "orchestrated"];
  const [editingSkill, setEditingSkill] = useState(null);
  const [categoryEditor, setCategoryEditor] = useState({});

  useEffect(() => {
    const next = {};
    categories.forEach((item) => {
      next[item.id] = { ...item };
    });
    setCategoryEditor(next);
  }, [categories]);

  function toggleCategoryBinding(skill, categoryId, checked) {
    const current = new Set(skill.category_bindings || []);
    if (checked) current.add(categoryId);
    else current.delete(categoryId);
    return Array.from(current);
  }

  return (
    <div className="page-grid">
      <div className="panel page-panel">
        <h3>Skill Library</h3>
        {groups.map((group) => (
          <div key={group} className="skill-group">
            <h4>{group}</h4>
            {skills
              .filter((item) => item.type === group)
              .map((skill) => (
                <details key={skill.id}>
                  <summary>{skill.name}</summary>
                  <p>{skill.description}</p>
                  <div className="checklist">
                    {categories.map((cat) => (
                      <label key={cat.id}>
                        <input
                          type="checkbox"
                          checked={(skill.category_bindings || []).includes(cat.id)}
                          onChange={(e) => {
                            const nextBindings = toggleCategoryBinding(
                              skill,
                              cat.id,
                              e.target.checked
                            );
                            onUpdateSkill(skill.id, {
                              name: skill.name,
                              description: skill.description,
                              content: skill.content,
                              category_bindings: nextBindings,
                            });
                          }}
                        />
                        {cat.name}
                      </label>
                    ))}
                  </div>
                  <button className="btn ghost" onClick={() => setEditingSkill(skill)}>
                    Edit Skill
                  </button>
                </details>
              ))}
          </div>
        ))}
      </div>

      <div className="panel page-panel">
        <h3>Task Category Defaults</h3>
        {categories.map((cat) => (
          <div key={cat.id} className="category-card">
            <input
              value={categoryEditor[cat.id]?.name || ""}
              onChange={(e) =>
                setCategoryEditor((prev) => ({
                  ...prev,
                  [cat.id]: { ...prev[cat.id], name: e.target.value },
                }))
              }
            />
            <textarea
              rows={2}
              value={categoryEditor[cat.id]?.description || ""}
              onChange={(e) =>
                setCategoryEditor((prev) => ({
                  ...prev,
                  [cat.id]: { ...prev[cat.id], description: e.target.value },
                }))
              }
            />
            <div className="checklist">
              {skills.map((skill) => (
                <label key={`${cat.id}-${skill.id}`}>
                  <input
                    type="checkbox"
                    checked={(categoryEditor[cat.id]?.default_skill_ids || []).includes(
                      skill.id
                    )}
                    onChange={(e) => {
                      const next = new Set(categoryEditor[cat.id]?.default_skill_ids || []);
                      if (e.target.checked) next.add(skill.id);
                      else next.delete(skill.id);
                      setCategoryEditor((prev) => ({
                        ...prev,
                        [cat.id]: {
                          ...prev[cat.id],
                          default_skill_ids: Array.from(next),
                        },
                      }));
                    }}
                  />
                  {skill.name}
                </label>
              ))}
            </div>
            <button
              className="btn"
              onClick={() => onUpdateCategory(cat.id, categoryEditor[cat.id])}
            >
              Save Category Binding
            </button>
          </div>
        ))}
      </div>

      {editingSkill && (
        <div className="modal">
          <div className="panel modal-content">
            <h3>Edit Skill</h3>
            <input
              value={editingSkill.name}
              onChange={(e) => setEditingSkill({ ...editingSkill, name: e.target.value })}
            />
            <textarea
              rows={3}
              value={editingSkill.description}
              onChange={(e) =>
                setEditingSkill({ ...editingSkill, description: e.target.value })
              }
            />
            <textarea
              rows={12}
              value={editingSkill.content}
              onChange={(e) => setEditingSkill({ ...editingSkill, content: e.target.value })}
            />
            <div className="modal-actions">
              <button className="btn ghost" onClick={() => setEditingSkill(null)}>
                Cancel
              </button>
              <button
                className="btn"
                onClick={async () => {
                  await onUpdateSkill(editingSkill.id, {
                    name: editingSkill.name,
                    description: editingSkill.description,
                    content: editingSkill.content,
                    category_bindings: editingSkill.category_bindings || [],
                  });
                  setEditingSkill(null);
                }}
              >
                Save Skill
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SkillLabPage({ tasks, onAnalyze, onApply, analysis }) {
  const [taskIds, setTaskIds] = useState([]);
  const [includeKnowledge, setIncludeKnowledge] = useState(true);
  return (
    <div className="panel page-panel">
      <h3>Skill Lab</h3>
      <div className="checklist">
        {tasks.map((task) => (
          <label key={task.id}>
            <input
              type="checkbox"
              checked={taskIds.includes(task.id)}
              onChange={(e) => {
                if (e.target.checked) setTaskIds([...taskIds, task.id]);
                else setTaskIds(taskIds.filter((id) => id !== task.id));
              }}
            />
            {task.name}
          </label>
        ))}
      </div>
      <label>
        <input
          type="checkbox"
          checked={includeKnowledge}
          onChange={(e) => setIncludeKnowledge(e.target.checked)}
        />
        Include Industry Knowledge
      </label>
      <button className="btn" onClick={() => onAnalyze(taskIds, includeKnowledge)}>
        Analyze Logs
      </button>
      {analysis && (
        <div>
          <p>{analysis.evidence_summary}</p>
          {analysis.suggestions.map((item) => (
            <div className="proposal-card" key={item.id}>
              <h4>
                {item.name} ({item.proposal_type})
              </h4>
              <p>{item.description}</p>
              <p>{item.rationale}</p>
              <button className="btn" onClick={() => onApply(item)}>
                Apply Proposal
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("chat");
  const [categories, setCategories] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [skills, setSkills] = useState([]);
  const [selectedTaskId, setSelectedTaskId] = useState("");
  const [messages, setMessages] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const selectedTask = useMemo(
    () => tasks.find((item) => item.id === selectedTaskId),
    [tasks, selectedTaskId]
  );

  async function refresh() {
    setErrorMessage("");
    const [categoryRes, taskRes, skillRes] = await Promise.allSettled([
      api.getCategories(),
      api.getTasks(),
      api.getSkills(),
    ]);

    if (categoryRes.status === "fulfilled") {
      setCategories(categoryRes.value);
    } else {
      setErrorMessage(categoryRes.reason?.message || "Failed to load task categories.");
    }

    if (taskRes.status === "fulfilled") {
      setTasks(taskRes.value);
      if (!selectedTaskId && taskRes.value.length) setSelectedTaskId(taskRes.value[0].id);
    } else {
      setErrorMessage(taskRes.reason?.message || "Failed to load tasks.");
    }

    if (skillRes.status === "fulfilled") {
      setSkills(skillRes.value);
    } else {
      setErrorMessage(skillRes.reason?.message || "Failed to load skills.");
    }
  }

  async function loadMessages(taskId) {
    if (!taskId) return;
    const data = await api.getTaskMessages(taskId);
    setMessages(data);
  }

  useEffect(() => {
    refresh().catch((error) => setErrorMessage(error.message));
  }, []);

  useEffect(() => {
    loadMessages(selectedTaskId).catch((error) => setErrorMessage(error.message));
  }, [selectedTaskId]);

  return (
    <div className="layout">
      <TaskSidebar
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTask={setSelectedTaskId}
        categories={categories}
        skills={skills}
        onCreateTask={async (payload) => {
          try {
            setErrorMessage("");
            await api.createTask(payload);
            await refresh();
          } catch (error) {
            setErrorMessage(error.message);
          }
        }}
      />
      <main className="main">
        {errorMessage && <div className="error-banner">{errorMessage}</div>}
        <div className="tabs">
          <button className={tab === "chat" ? "active" : ""} onClick={() => setTab("chat")}>
            Chat
          </button>
          <button
            className={tab === "library" ? "active" : ""}
            onClick={() => setTab("library")}
          >
            Skill Library
          </button>
          <button className={tab === "lab" ? "active" : ""} onClick={() => setTab("lab")}>
            Skill Lab
          </button>
        </div>

        {tab === "chat" && (
          <ChatPage
            selectedTask={selectedTask}
            messages={messages}
            onSend={async (text) => {
              if (!selectedTaskId) return;
              try {
                setErrorMessage("");
                await api.postTaskMessage(selectedTaskId, { content: text });
                await loadMessages(selectedTaskId);
              } catch (error) {
                setErrorMessage(error.message);
              }
            }}
          />
        )}
        {tab === "library" && (
          <SkillLibraryPage
            skills={skills}
            categories={categories}
            onUpdateSkill={async (skillId, payload) => {
              try {
                setErrorMessage("");
                await api.updateSkill(skillId, payload);
                await refresh();
              } catch (error) {
                setErrorMessage(error.message);
              }
            }}
            onUpdateCategory={async (categoryId, payload) => {
              try {
                setErrorMessage("");
                await api.updateCategory(categoryId, payload);
                await refresh();
              } catch (error) {
                setErrorMessage(error.message);
              }
            }}
          />
        )}
        {tab === "lab" && (
          <SkillLabPage
            tasks={tasks}
            analysis={analysis}
            onAnalyze={async (taskIds, includeIndustryKnowledge) => {
              try {
                setErrorMessage("");
                const result = await api.analyzeSkillLab({
                  task_ids: taskIds,
                  include_industry_knowledge: includeIndustryKnowledge,
                });
                setAnalysis(result);
              } catch (error) {
                setErrorMessage(error.message);
              }
            }}
            onApply={async (proposal) => {
              try {
                setErrorMessage("");
                await api.applySkillProposal(proposal);
                await refresh();
              } catch (error) {
                setErrorMessage(error.message);
              }
            }}
          />
        )}
      </main>
    </div>
  );
}

